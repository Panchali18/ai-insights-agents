"""Run the agent: collect → rank → draft → save a dated Markdown file.

Usage:
    python -m agent.main            # full run (uses the model)
    python -m agent.main --dry-run  # only check the sources; no model calls
    python -m agent.main --list-models  # show which models your key can use
"""

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

from agent.sources import collect

ROOT = Path(__file__).resolve().parent.parent


def needs_input(draft_text: str) -> bool:
    """True if the draft has open questions or placeholders for the author."""
    if "[YOUR EXPERIENCE" in draft_text:
        return True
    match = re.search(r"### Questions for you\s*(.*?)(\n### |\Z)", draft_text, re.S)
    if not match:
        return True  # missing section: treat as needing review
    return match.group(1).strip().lower().rstrip(".") not in ("none", "")


def status_for(post) -> str:
    if post.outcome == "rejected":
        return "Rejected by the quality gate (see the review below; kept for transparency)"
    if post.outcome == "unreviewed":
        return "Not reviewed by the quality gate (see the review notes below)"
    return "Needs your input" if needs_input(post.text) else "Ready for review"


def review_report(post) -> list:
    """The critic's findings on the final version, so the author sees why a draft passed or failed."""
    lines = ["### Quality gate review", ""]
    lines.append(f"- Outcome: **{post.outcome}** after {post.revisions} revision(s)")
    if post.note:
        lines.append(f"- Note: {post.note}")
    if not post.reviews:
        return lines + [""]

    final = post.reviews[-1]
    lines += ["", "| Criterion | Result | Reason |", "|---|---|---|"]
    for key in ("Q1", "Q2", "Q3", "Q4", "Q5", "Q6"):
        verdict = final.get("criteria", {}).get(key, {})
        mark = "✅" if verdict.get("pass") is True else "❌"
        reason = str(verdict.get("reason", "")).replace("|", "/").replace("\n", " ")
        lines.append(f"| {key} | {mark} | {reason} |")

    claims = final.get("claims", [])
    unsupported = [c.get("claim", "") for c in claims if c.get("supported") is not True]
    lines += ["", f"- Claims checked: {len(claims)}, unsupported: {len(unsupported)}"]
    lines += [f"  - Unsupported: {claim}" for claim in unsupported]
    if final.get("single_vendor_source"):
        lines.append("- ⚠ Single-vendor source: the only source is a company writing about its own products.")
    if post.outcome == "rejected":
        lines.append("- What still needed fixing:")
        lines += [f"  - {line}" for line in final.get("revision_instructions", [])]
    return lines + [""]


def source_report(result) -> list:
    lines = ["## Run summary", ""]
    lines.append(f"- Items collected: {len(result.items)}")
    read = ", ".join(
        f"{name} ({kept} item{'' if kept == 1 else 's'})" for name, kept in result.ok_sources
    )
    lines.append(f"- Sources read: {read or 'none'}")
    if result.failed_sources:
        lines.append("- Sources failed (skipped):")
        lines += [f"  - {name}: {reason}" for name, reason in result.failed_sources]
    else:
        lines.append("- Sources failed: none")
    if result.stale_sources:
        lines.append("- Sources that seem to have stopped publishing (check whether to replace them):")
        lines += [f"  - {name}: newest item {date}" for name, date in result.stale_sources]
    return lines


def main():
    parser = argparse.ArgumentParser(description="AI Insights Agent")
    parser.add_argument("--dry-run", action="store_true", help="check sources only, no model calls")
    parser.add_argument("--list-models", action="store_true", help="list models your API key can use")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    run = config["run"]

    if args.list_models:
        from agent.llm import LLM

        print("Models your key can use for text generation:")
        for name in LLM(config["model"]).list_models():
            print(f"  {name}")
        return

    print("Collecting from sources...")
    result = collect(
        config["sources"],
        run["lookback_days"],
        run.get("max_items_per_source", 15),
        run.get("stale_after_days", 21),
    )
    for name, kept in result.ok_sources:
        print(f"  ✓ {name}: {kept} recent item{'' if kept == 1 else 's'}")
    for name, reason in result.failed_sources:
        print(f"  ✗ {name}: skipped ({reason})")
    for name, date in result.stale_sources:
        print(f"  ⚠ {name}: may have stopped publishing (newest item {date})")

    if args.dry_run:
        print(f"\nDry run finished: {len(result.items)} items collected. No model calls made.")
        return
    if not result.items:
        raise SystemExit("No recent items collected, so there is nothing to draft.")

    from agent.llm import LLM
    from agent.steps import rank, write_post

    llm = LLM(config["model"])
    items = sorted(result.items, key=lambda i: i.published, reverse=True)[: run["max_items_to_rank"]]

    print(f"\nRanking {len(items)} items...")
    selected = rank(llm, items, run["drafts_per_run"])
    if not selected:
        raise SystemExit("The ranking step returned no usable items.")

    sections = []
    for number, (item, scores) in enumerate(selected, start=1):
        print(f"Drafting and reviewing: {item.title}")
        post = write_post(llm, item, run.get("max_revisions", 1))
        print(f"  Quality gate: {post.outcome} after {post.revisions} revision(s)")
        sections += [
            f"## Draft {number}: {item.title}",
            "",
            f"**Status:** {status_for(post)}  ",
            f"**Label:** {scores.get('label', '?')} · **Scores:** recency {scores.get('recency')}, "
            f"momentum {scores.get('momentum')}, relevance {scores.get('relevance')}  ",
            f"**Why this topic:** {scores.get('reason', '')}  ",
            f"**Grounded on:** {'full article' if post.grounded_on_article else 'feed summary only (article page could not be read)'}",
            "",
            post.text.strip(),
            "",
        ] + review_report(post)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = ROOT / run["output_dir"]
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{today}.md"
    run_number = 2
    while output_file.exists():  # never overwrite an earlier run from the same day
        output_file = output_dir / f"{today}-{run_number}.md"
        run_number += 1

    header = [
        f"# Drafts for {today}",
        "",
        f"Model: {config['model']['provider']} / {config['model']['name']} · "
        f"Model calls: {llm.calls_made} of {llm.max_calls} allowed",
        "",
        "> Drafts are for review only. Nothing here has been posted.",
        "",
    ]
    output_file.write_text("\n".join(header + sections + source_report(result)) + "\n", encoding="utf-8")
    print(f"\nDone. Drafts saved to {output_file.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
