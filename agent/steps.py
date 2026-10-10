"""The agent's reasoning steps: rank items, then draft a post."""

import json
from pathlib import Path

from agent.llm import LLM
from agent.sources import Item, fetch_article_text

PROMPTS = Path(__file__).resolve().parent.parent / "prompts"


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


def draft(llm: LLM, item: Item) -> tuple:
    """Write one post draft for an item. Returns (draft_markdown, grounded_on_full_article)."""
    article = fetch_article_text(item.url)
    material = article if len(article) > len(item.summary) else item.summary
    prompt = (
        _load_prompt("draft.md")
        .replace("{title}", item.title)
        .replace("{source}", item.source)
        .replace("{published}", item.published)
        .replace("{url}", item.url)
        .replace("{material}", material)
    )
    return llm.generate(prompt), bool(article)
