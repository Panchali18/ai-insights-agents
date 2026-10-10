"""Run the agent: collect → rank → draft → save a dated Markdown file.

Usage:
    python -m agent.main            # full run (uses the model)
    python -m agent.main --dry-run  # only check the sources; no model calls
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


def source_report(result) -> list:
    lines = ["## Run summary", ""]
    lines.append(f"- Items collected: {len(result.items)}")
    read = ", ".join(f"{name} ({kept} items)" for name, kept in result.ok_sources)
    lines.append(f"- Sources read: {read or 'none'}")
    if result.failed_sources:
        lines.append("- Sources failed (skipped):")
        lines += [f"  - {name}: {reason}" for name, reason in result.failed_sources]
    else:
        lines.append("- Sources failed: none")
    return lines


def main():
    parser = argparse.ArgumentParser(description="AI Insights Agent")
    parser.add_argument("--dry-run", action="store_true", help="check sources only, no model calls")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    run = config["run"]

    print("Collecting from sources...")
    result = collect(config["sources"], run["lookback_days"], run.get("max_items_per_source", 15))
    for name, kept in result.ok_sources:
        print(f"  ✓ {name}: {kept} recent item{'' if kept == 1 else 's'}")
    for name, reason in result.failed_sources:
        print(f"  ✗ {name}: skipped ({reason})")

    if args.dry_run:
        print(f"\nDry run finished: {len(result.items)} items collected. No model calls made.")
        return
    if not result.items:
        raise SystemExit("No recent items collected, so there is nothing to draft.")

    from agent.llm import LLM
    from agent.steps import draft, rank

    llm = LLM(config["model"])
    items = sorted(result.items, key=lambda i: i.published, reverse=True)[: run["max_items_to_rank"]]

    print(f"\nRanking {len(items)} items...")
    selected = rank(llm, items, run["drafts_per_run"])
    if not selected:
        raise SystemExit("The ranking step returned no usable items.")

    sections = []
    for number, (item, scores) in enumerate(selected, start=1):
        print(f"Drafting: {item.title}")
        text, grounded = draft(llm, item)
        status = "Needs your input" if needs_input(text) else "Ready for review"
        sections += [
            f"## Draft {number}: {item.title}",
            "",
            f"**Status:** {status}  ",
            f"**Label:** {scores.get('label', '?')} · **Scores:** recency {scores.get('recency')}, "
            f"momentum {scores.get('momentum')}, relevance {scores.get('relevance')}  ",
            f"**Why this topic:** {scores.get('reason', '')}  ",
            f"**Grounded on:** {'full article' if grounded else 'feed summary only (article page could not be read)'}",
            "",
            text.strip(),
            "",
        ]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = ROOT / run["output_dir"]
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / f"{today}.md"

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
