"""The agent's reasoning steps: rank items, then write a post through a draft → critique → revise loop."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from agent.llm import LLM, CallLimitReached
from agent.sources import Item, fetch_article_text

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"
CRITERIA = ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6")


def _load_prompt(name: str) -> str:
    return (PROMPTS / name).read_text(encoding="utf-8")


def rank(llm: LLM, items: list, top_n: int) -> list:
    """Score every item and return the top_n as (item, scores) pairs (US-2.1)."""
    listing = "\n\n".join(
        f"[id {i.id}] {i.title}\nSource: {i.source} ({i.group}), published {i.published}\n"
        f"Summary: {i.summary}"
        for i in items
    )
    prompt = _load_prompt("rank.md").replace("{items}", listing)
    reply = llm.generate(prompt, want_json=True)

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


@dataclass
class PostResult:
    text: str
    grounded_on_article: bool
    reviews: list = field(default_factory=list)  # one critic review per round
    revisions: int = 0
    outcome: str = "unreviewed"  # passed | rejected | unreviewed
    note: str = ""


def _passes(review: dict) -> bool:
    """Decide from the critic's own findings, not only its stated verdict: a draft passes only
    if every criterion passes and every claim is supported."""
    criteria = review.get("criteria", {})
    all_pass = all(criteria.get(c, {}).get("pass") is True for c in CRITERIA)
    claims_ok = all(claim.get("supported") is True for claim in review.get("claims", []))
    return all_pass and claims_ok


def critique(llm: LLM, material: str, draft_text: str) -> dict:
    """Ask a separate critic call to judge the draft (US-4.1, US-4.2). Returns {} if unusable."""
    prompt = _load_prompt("critic.md").replace("{material}", material).replace("{draft}", draft_text)
    reply = llm.generate(prompt, want_json=True)
    try:
        review = json.loads(reply)
    except json.JSONDecodeError:
        return {}
    return review if isinstance(review, dict) and "criteria" in review else {}


def write_post(llm: LLM, item: Item, max_revisions: int = 1) -> PostResult:
    """Draft a post, then let the critic decide: pass it, send it back for revision, or reject it."""
    article = fetch_article_text(item.url)
    material = article if len(article) > len(item.summary) else item.summary
    draft_prompt = (
        _load_prompt("draft.md")
        .replace("{title}", item.title)
        .replace("{source}", item.source)
        .replace("{published}", item.published)
        .replace("{url}", item.url)
        .replace("{material}", material)
    )

    result = PostResult(text=llm.generate(draft_prompt), grounded_on_article=bool(article))

    while True:
        try:
            review = critique(llm, material, result.text)
        except CallLimitReached:
            result.note = "The call limit was reached before the critic could review this version."
            return result
        if not review:
            result.note = "The critic's reply couldn't be read, so this version is unreviewed."
            return result
        result.reviews.append(review)

        if _passes(review):
            result.outcome = "passed"
            return result
        if result.revisions >= max_revisions:
            result.outcome = "rejected"
            return result

        instructions = review.get("revision_instructions") or ["Fix the failed criteria listed by the reviewer."]
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
