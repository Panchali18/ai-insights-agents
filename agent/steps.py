"""The agent's reasoning steps: rank items, then write a post through a draft → critique → revise loop."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from agent.llm import LLM, CallLimitReached
from agent import style
from agent.sources import Item, fetch_article

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
CRITERIA = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6")


def _load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def rank(llm: LLM, items: list, top_n: int) -> list:
    """Score every item and return the top_n as (item, scores) pairs (US-2.1)."""
    # Ranking only needs the gist, so summaries are trimmed to keep this, the largest request, light.
    listing = "\n\n".join(
        f"[id {i.id}] {i.title}\nSource: {i.source} ({i.group}), published {i.published}\n"
        f"Summary: {i.summary[:250]}"
        for i in items
    )
    prompt = _load_prompt("rank.md").replace("{items}", listing)
    reply = llm.generate(prompt, want_json=True, model=llm.ranking_model)

    try:
        scored = json.loads(reply)["items"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise SystemExit(f"The ranking step returned something that isn't valid JSON: {reply[:300]}") from error

    by_id = {i.id: i for i in items}
    results = []
    for entry in scored:
        item = by_id.get(entry.get("id"))
        if not item:
            continue  # ignore ids the model invented
        total = sum(int(entry.get(k, 0)) for k in ("recency", "momentum", "relevance"))
        entry["total"] = total
        results.append((item, entry))

    results.sort(key=lambda pair: (pair[1].get("relevance", 0), pair[1]["total"]), reverse=True)
    return results[:top_n]


SOURCE_NOTES = {
    "full article": "The full source page was read.",
    "social media post": (
        "The source is a social media post, not an article. Attribute every claim to the poster by "
        "name. Add a question asking the author to confirm the key facts with a second source."
    ),
    "feed summary": (
        "Only the feed summary could be read, not the full page. Stay strictly within it and add a "
        "question asking the author to check the original."
    ),
}
MIN_SUMMARY_CHARS = 200  # below this, a feed summary is too thin to draft from


@dataclass
class PostResult:
    text: str
    grounded_on: str  # what the agent actually read: full article, social media post, feed summary
    reviews: list = field(default_factory=list)  # one critic review per round
    style_findings: list = field(default_factory=list)  # code-detected rule breaks, final version
    revisions: int = 0
    outcome: str = "unreviewed"  # passed | rejected | unreviewed
    note: str = ""


@dataclass
class Material:
    text: str
    grounded_on: str


def gather_material(item: Item):
    """Read the item's source page. Returns None if there's nothing reliable enough to draft from,
    so the caller can move on to the next-ranked topic instead of drafting from a headline."""
    article = fetch_article(item.url)
    if article.usable and len(article.text) > len(item.summary):
        return Material(article.text, article.kind)
    if len(item.full_text) >= 1500:  # many newsletter feeds include the whole article
        return Material(item.full_text, "full article")
    if len(item.summary) >= MIN_SUMMARY_CHARS and not item.summary.startswith("Hacker News story with"):
        return Material(item.summary, "feed summary")
    return None


def _passes(review: dict, style_findings: list) -> bool:
    """Decide from the findings, not the critic's stated verdict: a draft passes only if every
    criterion passes, every claim is supported, and code found no style-rule breaks."""
    criteria = review.get("criteria", {})
    all_pass = all(criteria.get(c, {}).get("pass") is True for c in CRITERIA)
    claims_ok = all(claim.get("supported") is True for claim in review.get("claims", []))
    return all_pass and claims_ok and not style_findings


def _source_facts(material: Material, item: Item, style_findings: list) -> str:
    lines = [
        f"- What the agent read: {material.grounded_on} ({len(material.text)} characters).",
        f"- Source: {item.source}. URL: {item.url}",
        "- Number of sources the draft can draw on: 1.",
    ]
    if style_findings:
        lines.append("- Style-rule breaks found by code in the post text (Q6 must fail):")
        lines += [f"  - {finding}" for finding in style_findings]
    else:
        lines.append("- Style-rule breaks found by code: none.")
    return "\n".join(lines)


def critique(llm: LLM, material: Material, item: Item, draft_text: str, style_findings: list) -> dict:
    """Ask a separate critic call to judge the draft (US-4.1, US-4.2). Returns {} if unusable."""
    prompt = (
        _load_prompt("critic.md")
        .replace("{source_facts}", _source_facts(material, item, style_findings))
        .replace("{style_guide}", _load_prompt("style-guide.md"))
        .replace("{material}", material.text)
        .replace("{draft}", draft_text)
    )
    reply = llm.generate(prompt, want_json=True)
    try:
        review = json.loads(reply)
    except json.JSONDecodeError:
        return {}
    if not (isinstance(review, dict) and "criteria" in review):
        return {}
    if style_findings:  # code overrides the model on clear-cut rule breaks
        review["criteria"]["Q6"] = {"pass": False, "reason": "Code found: " + " ".join(style_findings)}
    return review


def write_post(llm: LLM, item: Item, material: Material, max_revisions: int = 1) -> PostResult:
    """Draft a post, then let the critic decide: pass it, send it back for revision, or reject it."""
    draft_prompt = (
        _load_prompt("draft.md")
        .replace("{source_note}", SOURCE_NOTES[material.grounded_on])
        .replace("{style_guide}", _load_prompt("style-guide.md"))
        .replace("{title}", item.title)
        .replace("{source}", item.source)
        .replace("{published}", item.published)
        .replace("{url}", item.url)
        .replace("{material}", material.text)
    )

    result = PostResult(text=llm.generate(draft_prompt), grounded_on=material.grounded_on)

    while True:
        result.style_findings = style.check(result.text)
        try:
            review = critique(llm, material, item, result.text, result.style_findings)
        except CallLimitReached:
            result.note = "The call limit was reached before the critic could review this version."
            return result
        if not review:
            result.note = "The critic's reply couldn't be read, so this version is unreviewed."
            return result
        result.reviews.append(review)

        if _passes(review, result.style_findings):
            result.outcome = "passed"
            return result
        if result.revisions >= max_revisions:
            result.outcome = "rejected"
            return result

        instructions = list(review.get("revision_instructions") or [])
        instructions += [f"Style rule: {finding}" for finding in result.style_findings]
        if not instructions:
            instructions = ["Fix the failed criteria listed by the reviewer."]
        revise_prompt = draft_prompt + _load_prompt("revise.md").replace(
            "{instructions}", "\n".join(f"- {line}" for line in instructions)
        ).replace("{draft}", result.text)
        try:
            result.text = llm.generate(revise_prompt)
        except CallLimitReached:
            result.outcome = "rejected"
            result.note = "The call limit was reached before the draft could be revised."
            return result
        result.revisions += 1
