"""Run the agent in two steps.

1. Pitch:  collect → rank → read the top topics → write short pitches for the author to choose from.
2. Draft:  write the chosen pitch as a post, then review it through the quality gate.

Usage:
    python -m agent.main                 # step 1: pitches, saved to drafts/<date>-pitches.md
    python -m agent.main --draft 2       # step 2: draft pitch 2 from the latest pitches file
    python -m agent.main --dry-run       # only check the sources; no model calls
    python -m agent.main --list-models   # show which models your key can use
"""

import argparse
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import yaml

from agent.sources import Item, collect

ROOT = Path(__file__).resolve().parent.parent


def _section(draft_text: str, heading: str) -> str:
    match = re.search(rf"### {re.escape(heading)}\s*(.*?)(?=\n### |\Z)", draft_text, re.S)
    return match.group(1).strip() if match else ""


def _is_empty(text: str) -> bool:
    return text.strip().lower().rstrip(".") in ("", "none", "nothing")


def must_check(draft_text: str) -> bool:
    """True if the draft lists facts the author must verify before posting."""
    return not _is_empty(_section(draft_text, "Before posting"))


def status_for(post) -> str:
    if post.outcome == "rejected":
        return "Rejected by the quality gate (see the review below; kept for transparency)"
    if post.outcome == "unreviewed":
        return "Not reviewed by the quality gate (see the review notes below)"
    if must_check(post.text):
        return "Check before posting (see 'Before posting')"
    if post.outcome == "passed with quick fixes":
        return "Ready to post after quick fixes (see the review below)"
    return "Ready to post"


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
    names = {"Q1": "Takeaway", "Q2": "Specific", "Q3": "Learner's voice", "Q4": "Grounded and fair",
             "Q5": "Postable", "Q6": "Style (minor)", "Q7": "Holds for readers"}
    for key, name in names.items():
        verdict = final.get("criteria", {}).get(key, {})
        mark = "✅" if verdict.get("pass") is True else ("⚠️" if key == "Q6" else "❌")
        reason = str(verdict.get("reason", "")).replace("|", "/").replace("\n", " ")
        lines.append(f"| {key} {name} | {mark} | {reason} |")

    claims = final.get("claims", [])
    unsupported = [c.get("claim", "") for c in claims if c.get("supported") is not True]
    lines += ["", f"- Claims checked: {len(claims)}, unsupported: {len(unsupported)}"]
    lines += [f"  - Unsupported: {claim}" for claim in unsupported]
    if final.get("unconfirmed_social_source"):
        lines.append("- ⚠ Social media source: confirm the key facts with a second source before posting.")
    if final.get("single_vendor_source"):
        lines.append("- ⚠ Single-vendor source: the only source is a company writing about its own products.")
    elif final.get("single_source"):
        lines.append("- ⚠ Single source: the post rests on one source.")

    quick = list(post.style_findings) + list(final.get("quick_fixes") or [])
    if quick and post.outcome != "rejected":
        lines.append("- Quick fixes before posting:")
        lines += [f"  - {fix}" for fix in quick]
    if post.outcome == "rejected":
        still = list(final.get("revision_instructions") or []) + list(post.major_failures)
        if still:
            lines.append("- What still needed fixing:")
            lines += [f"  - {line}" for line in still]
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


def _new_file(output_dir: Path, stem: str, suffix: str) -> Path:
    """A file path that never overwrites an earlier run from the same day."""
    path = output_dir / f"{stem}{suffix}"
    n = 2
    while path.exists():
        path = output_dir / f"{stem}-{n}{suffix}"
        n += 1
    return path


def run_pitches(config: dict, result) -> None:
    from agent.llm import LLM
    from agent.steps import gather_material, pitch, rank

    run = config["run"]
    llm = LLM(config["model"])
    items = sorted(result.items, key=lambda i: i.published, reverse=True)[: run["max_items_to_rank"]]
    wanted = run.get("pitches_per_run", 3)

    print(f"\nRanking {len(items)} items...")
    ranked = rank(llm, items, wanted + run.get("spare_candidates", 3))
    if not ranked:
        raise SystemExit("The ranking step returned no usable items.")

    candidates, skipped = [], []
    for item, _scores in ranked:
        if len(candidates) >= wanted:
            break
        material = gather_material(item)
        if material is None:
            print(f"Skipping (couldn't read the source properly): {item.title}")
            skipped.append(item)
            continue
        candidates.append((item, material))
    if not candidates:
        raise SystemExit("None of the top-ranked topics had a readable source, so there's nothing to pitch.")

    print(f"Writing {len(candidates)} pitches...")
    pitches = pitch(llm, candidates)

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_dir = ROOT / run["output_dir"]
    output_dir.mkdir(exist_ok=True)
    md_file = _new_file(output_dir, f"{today}-pitches", ".md")
    state_file = md_file.with_suffix(".json")

    lines = [f"# Pitches for {today}", "",
             "Pick one, then run `python -m agent.main --draft <number>`. Or pick none: no post is fine.", ""]
    for n, p in enumerate(pitches, start=1):
        item = p["item"]
        lines += [
            f"## {n}. {p.get('idea', item.title)}",
            "",
            f"- **Angle:** {p.get('angle', '?')} · **Fit:** {p.get('fit', '?')}/5",
            f"- **Why readers would care:** {p.get('why_readers_care', '')}",
            f"- **Connects to your work:** {p.get('connection', 'None')}",
            f"- **Possible first line:** {p.get('opening_line', '')}",
            f"- **Source:** [{item.title}]({item.url}) ({item.source}, {item.published}; read: {p['material'].grounded_on})",
            "",
        ]
    if skipped:
        lines += ["## Topics skipped", "", "Ranked highly, but the source was blocked or too thin to use:", ""]
        lines += [f"- [{i.title}]({i.url}) ({i.source})" for i in skipped]
        lines.append("")
    lines += [f"Model calls: {llm.calls_made} of {llm.max_calls} allowed", ""] + source_report(result)
    md_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    state = [{k: v for k, v in p.items() if k not in ("item", "material")}
             | {"item": asdict(p["item"]), "material": asdict(p["material"])} for p in pitches]
    state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

    print()
    for n, p in enumerate(pitches, start=1):
        print(f"  {n}. [{p.get('angle', '?')}, fit {p.get('fit', '?')}/5] {p.get('idea', p['item'].title)}")
    print(f"\nPitches saved to {md_file.relative_to(ROOT)}")
    print("To draft one, run:  python -m agent.main --draft <number>")


def run_draft(config: dict, number: int) -> None:
    from agent.llm import LLM
    from agent.steps import Material, write_post

    run = config["run"]
    output_dir = ROOT / run["output_dir"]
    state_files = sorted(output_dir.glob("*-pitches*.json"), key=lambda f: f.stat().st_mtime)
    if not state_files:
        raise SystemExit("No pitches found. Run `python -m agent.main` first.")
    state = json.loads(state_files[-1].read_text(encoding="utf-8"))
    if not 1 <= number <= len(state):
        raise SystemExit(f"Pick a pitch between 1 and {len(state)} from {state_files[-1].name}.")

    chosen = state[number - 1]
    item, material = Item(**chosen["item"]), Material(**chosen["material"])
    llm = LLM(config["model"])
    print(f"Drafting and reviewing pitch {number}: {chosen.get('idea', item.title)}  [{material.grounded_on}]")
    post = write_post(llm, item, material, chosen, run.get("max_revisions", 1))
    print(f"  Quality gate: {post.outcome} after {post.revisions} revision(s)")

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    output_file = _new_file(output_dir, f"{today}-draft", ".md")
    lines = [
        f"# Draft for {today}: {chosen.get('idea', item.title)}",
        "",
        f"**Status:** {status_for(post)}  ",
        f"**Angle:** {chosen.get('angle', '?')} · **From pitch:** {number} in {state_files[-1].name}  ",
        f"**Source:** [{item.title}]({item.url}) ({item.source}; read: {post.grounded_on})  ",
        f"Model: {config['model']['provider']} / {config['model']['name']} · "
        f"Model calls: {llm.calls_made} of {llm.max_calls} allowed",
        "",
        "> For review only. Nothing here has been posted.",
        "",
        post.text.strip(),
        "",
    ] + review_report(post)
    output_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDone. Draft saved to {output_file.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description="AI Insights Agent")
    parser.add_argument("--dry-run", action="store_true", help="check sources only, no model calls")
    parser.add_argument("--list-models", action="store_true", help="list models your API key can use")
    parser.add_argument("--draft", type=int, metavar="N", help="draft pitch N from the latest pitches")
    args = parser.parse_args()

    config = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    run = config["run"]

    if args.list_models:
        from agent.llm import LLM

        print("Models your key can use for text generation:")
        for name in LLM(config["model"]).list_models():
            print(f"  {name}")
        return
    if args.draft is not None:
        run_draft(config, args.draft)
        return

    print("Collecting from sources...")
    result = collect(
        config["sources"],
        run["lookback_days"],
        run.get("max_items_per_source", 15),
        run.get("stale_after_days", 21),
        run.get("group_caps"),
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
        raise SystemExit("No recent items collected, so there is nothing to pitch.")
    run_pitches(config, result)


if __name__ == "__main__":
    main()
