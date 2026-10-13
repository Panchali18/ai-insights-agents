"""The agent's reasoning steps: rank items, then write a post through a draft → critique → revise loop."""

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from agent.llm import LLM, CallLimitReached
from agent import style
from agent.sources import Item, fetch_article

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
CRITERIA = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6", "Q7")


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
        "name. Under 'Before posting', list any facts that need confirming with a second source; "
        "a named person's stated opinion or estimate, attributed to them, needs no confirmation."
    ),
    "feed summary": (
        "Only the feed summary could be read, not the full page. Stay strictly within it, and under "
        "'Before posting' ask the author to check the original."
    ),
}
MIN_SUMMARY_CHARS = 200  # below this, a feed summary is too thin to draft from
MAJOR = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q7")  # block a draft
MINOR = ("Q6",)  # listed as quick fixes, never block
ROOT = PROMPTS.parent


def author_notes() -> str:
    return _load_prompt("author.md")


def build_log(max_rows: int = 15) -> str:
    """The most recent build timeline steps, as plain lines: what was done and what happened.
    This is the only source of facts about the author's own work."""
    path = ROOT / "docs" / "decisions.md"
    if not path.exists():
        return "No build log available."
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 5 and cells[0].isdigit():
            number, date, did, happened, _ = cells
            if happened.lower() != "pending":
                rows.append(f"- Step {number} ({date}): {did}. Result: {happened}")
    return "\n".join(rows[-max_rows:]) or "No build log available."


@dataclass
class PostResult:
    text: str
    grounded_on: str  # what the agent actually read: full article, social media post, feed summary
    reviews: list = field(default_factory=list)  # one critic review per round
    style_findings: list = field(default_factory=list)  # code-detected style breaks, final version
    major_failures: list = field(default_factory=list)  # failed major criteria, final version
    revisions: int = 0
    outcome: str = "unreviewed"  # passed | passed with quick fixes | rejected | unreviewed
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


def pitch(llm: LLM, candidates: list) -> list:
    """Turn readable candidates [(item, material)] into short pitches the author can judge quickly.
    Returns pitches sorted by fit, each with its item and material attached."""
    listing = "\n\n".join(
        f"[candidate {n}] {item.title}\nSource: {item.source}, published {item.published}\n"
        f"Material: {material.text[:1500]}"
        for n, (item, material) in enumerate(candidates, start=1)
    )
    prompt = (
        _load_prompt("pitch.md")
        .replace("{author}", author_notes())
        .replace("{style_guide}", _load_prompt("style-guide.md"))
        .replace("{build_log}", build_log())
        .replace("{candidates}", listing)
    )
    reply = llm.generate(prompt, want_json=True)
    try:
        raw = json.loads(reply)["pitches"]
    except (json.JSONDecodeError, KeyError, TypeError) as error:
        raise SystemExit(f"The pitch step returned something that isn't valid JSON: {reply[:300]}") from error

    pitches = []
    for entry in raw:
        n = entry.get("candidate")
        if not isinstance(n, int) or not 1 <= n <= len(candidates):
            continue  # ignore candidates the model invented
        item, material = candidates[n - 1]
        entry["item"], entry["material"] = item, material
        pitches.append(entry)
    pitches.sort(key=lambda p: int(p.get("fit", 0) or 0), reverse=True)
    return pitches


def _code_findings(draft_text: str) -> tuple:
    """(major, minor) problems code can find without a model."""
    post = style.post_text(draft_text)
    major = []
    if re.search(r"\[(?:YOUR|ADD|INSERT|TODO)[^\]]*\]", post, re.I):
        major.append("Q5: the post has a placeholder to fill in.")
    return major, style.check(draft_text)


def _major_failures(review: dict, code_major: list) -> list:
    criteria = review.get("criteria", {})
    failed = [f"{c}: {criteria.get(c, {}).get('reason', 'failed')}" for c in MAJOR
              if criteria.get(c, {}).get("pass") is not True]
    failed += [f"Unsupported claim: {c.get('claim', '')}" for c in review.get("claims", [])
               if c.get("supported") is not True]
    return failed + code_major


def _source_facts(material: Material, item: Item, style_findings: list, code_major: list) -> str:
    lines = [
        f"- What the agent read: {material.grounded_on} ({len(material.text)} characters).",
        f"- Source: {item.source}. URL: {item.url}",
        "- Number of sources the draft can draw on: 1.",
    ]
    lines += [f"- Found by code (major): {finding}" for finding in code_major]
    if style_findings:
        lines.append("- Style breaks found by code (minor, Q6):")
        lines += [f"  - {finding}" for finding in style_findings]
    else:
        lines.append("- Style breaks found by code: none.")
    return "\n".join(lines)


def critique(llm: LLM, material: Material, item: Item, draft_text: str, style_findings: list,
             code_major: list = ()) -> dict:
    """Ask a separate critic call to judge the draft (US-4.1, US-4.2). Returns {} if unusable."""
    prompt = (
        _load_prompt("critic.md")
        .replace("{author}", author_notes())
        .replace("{source_facts}", _source_facts(material, item, style_findings, list(code_major)))
        .replace("{style_guide}", _load_prompt("style-guide.md"))
        .replace("{build_log}", build_log())
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
    if style_findings:  # code overrides the model on clear-cut style breaks (still minor)
        review["criteria"]["Q6"] = {"pass": False, "reason": "Code found: " + " ".join(style_findings)}
    return review


def write_post(llm: LLM, item: Item, material: Material, chosen: dict = None,
               max_revisions: int = 1) -> PostResult:
    """Draft a post, then let the critic decide. Major problems send it back for revision, and it's
    rejected if they remain. Minor style points never block; they're listed as quick fixes."""
    chosen = chosen or {}
    draft_prompt = (
        _load_prompt("draft.md")
        .replace("{author}", author_notes())
        .replace("{angle}", chosen.get("angle", "read and learned"))
        .replace("{connection}", chosen.get("connection", "None"))
        .replace("{source_note}", SOURCE_NOTES[material.grounded_on])
        .replace("{style_guide}", _load_prompt("style-guide.md"))
        .replace("{build_log}", build_log())
        .replace("{title}", item.title)
        .replace("{source}", item.source)
        .replace("{published}", item.published)
        .replace("{url}", item.url)
        .replace("{material}", material.text)
    )

    result = PostResult(text=llm.generate(draft_prompt), grounded_on=material.grounded_on)

    while True:
        code_major, result.style_findings = _code_findings(result.text)
        try:
            review = critique(llm, material, item, result.text, result.style_findings, code_major)
        except CallLimitReached:
            result.note = "The call limit was reached before the critic could review this version."
            return result
        if not review:
            result.note = "The critic's reply couldn't be read, so this version is unreviewed."
            return result
        result.reviews.append(review)
        result.major_failures = _major_failures(review, code_major)

        if not result.major_failures:
            minor = result.style_findings or review.get("quick_fixes") or \
                review["criteria"].get("Q6", {}).get("pass") is not True
            result.outcome = "passed with quick fixes" if minor else "passed"
            return result
        if result.revisions >= max_revisions:
            result.outcome = "rejected"
            return result

        instructions = list(review.get("revision_instructions") or [])
        instructions += [f"Fix: {failure}" for failure in code_major]
        instructions += [f"Style rule: {finding}" for finding in result.style_findings]
        instructions += [f"Small fix: {fix}" for fix in review.get("quick_fixes") or []]
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
