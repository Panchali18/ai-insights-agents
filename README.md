# ai-insights-agents

Research-to-post AI agent that turns AI news and real practitioner pain points into well-sourced LinkedIn drafts, using a self-critique quality gate, cited claims and a human approval step. No generic AI content.

> **Status: in development.** Collecting, ranking and the critic-and-revise loop have run for real. The pitch-then-draft flow and the learner-voice quality bar are built and tested with sample data; their first real run is pending. Voice, content pillars and evaluation come later; see the [delivery phases](docs/requirements.md#8-delivery-phases).

## How it works

1. **Collect:** reads recent items from an approved list of sources ([docs/sources.md](docs/sources.md)). A failing source is logged and skipped, never fatal.
2. **Rank:** a lighter model scores each item for the target readers (hiring managers for AI roles, teams adopting AI, analysts and product owners).
3. **Read:** the agent reads each top topic's source and records honestly what it got (full article, social media post, or feed summary). Topics it can't read properly are skipped.
4. **Pitch:** it writes 3 one-line pitches, each linked where possible to the author's own build log, with an angle and a fit score. The author picks one, or none.
5. **Draft:** `--draft N` writes the chosen pitch in the author's voice: a learner sharing what she tried, read, got wrong or is still working out. The draft is postable as written; facts to check and optional personal touches are listed separately.
6. **Critique and revise:** a separate model call checks 7 criteria. Major problems (wrong or unfair claims, advice that doesn't hold for readers, an expert's voice, gaps to fill) send the draft back once, then reject it. Minor style points are listed as quick fixes. Plain code catches clear-cut style breaks and placeholders, and the code decides from the critic's findings rather than its stated verdict.

The agent cannot post anywhere. A human reviews every draft.

## Design choices

- **Model-agnostic:** the provider and model are set in `config.yaml`; the agent's logic calls one `generate` function. It currently runs on Gemini's free tier.
- **Prompts as files:** the ranking and drafting instructions live in `prompts/`, so they can be reviewed and versioned like code.
- **Prompt-injection defence:** fetched web content is wrapped as data and the model is told never to follow instructions inside it.
- **Cost cap:** a hard limit on model calls per run (`max_calls_per_run`).
- **Right-sized models:** ranking uses a lighter model; drafting and reviewing use the main one. A fallback model takes over if Google's servers fail.

## Project structure

```
agent/          the agent code (sources, model wrapper, steps, main run)
prompts/        ranking and drafting instructions sent to the model
docs/           requirements, sources, reference library
drafts/         output: one Markdown file per run
config.yaml     model, run settings and source list
```

## Running it

Requires a free Gemini API key from Google AI Studio, stored as a Codespaces secret named `GEMINI_API_KEY`.

```bash
pip install -r requirements.txt
python -m agent.main --dry-run   # check the sources only; no model calls
python -m agent.main             # pitches; writes drafts/<date>-pitches.md
python -m agent.main --draft 2   # draft pitch 2; writes drafts/<date>-draft.md
```

## Documentation

- [Requirements](docs/requirements.md): user stories, acceptance criteria, guardrails and phases
- [Sources](docs/sources.md): the approved sources, exclusions and research findings
- [Reference library](docs/reference-library.md): reports and standards drafts can cite
- [Build timeline and decision log](docs/decisions.md): every build step in order, and the reasoning behind each decision

Built with Claude.
