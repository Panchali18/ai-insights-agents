# ai-insights-agents

Research-to-post AI agent that turns AI news and real practitioner pain points into well-sourced LinkedIn drafts, using a self-critique quality gate, cited claims and a human approval step. No generic AI content.

> **Status: in development.** Phase 1 (collect → rank → draft) works. Phase 2's critic-and-revise loop is built and tested with sample data; its first real run is pending. Voice, content pillars and evaluation come later; see the [delivery phases](docs/requirements.md#8-delivery-phases).

## How it works

1. **Collect:** reads recent items from an approved list of sources ([docs/sources.md](docs/sources.md)). A failing source is logged and skipped, never fatal.
2. **Rank:** the model labels each item as *News* or *Pain point* and scores it on recency, momentum and relevance, then the top item is chosen.
3. **Draft:** the agent reads the full article and drafts a post against a six-point quality bar. Anything it can't verify, or that needs the author's own experience, becomes a question for the author instead of a guess.
4. **Critique and revise:** a separate model call reviews the draft against the quality bar, checks each claim against the source, and flags AI-writing tells and single-vendor sourcing. The review decides what happens next: pass, revise once, or reject. The code reads the critic's findings rather than trusting its stated verdict.
5. **Save:** one dated Markdown file in `drafts/`, with each draft's status, scores, sources, the critic's review and a run summary.

The agent cannot post anywhere. A human reviews every draft.

## Design choices

- **Model-agnostic:** the provider and model are set in `config.yaml`; the agent's logic calls one `generate` function. It currently runs on Gemini's free tier.
- **Prompts as files:** the ranking and drafting instructions live in `prompts/`, so they can be reviewed and versioned like code.
- **Prompt-injection defence:** fetched web content is wrapped as data and the model is told never to follow instructions inside it.
- **Cost cap:** a hard limit on model calls per run (`max_calls_per_run`).

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
python -m agent.main             # full run; writes drafts/<date>.md
```

## Documentation

- [Requirements](docs/requirements.md): user stories, acceptance criteria, guardrails and phases
- [Sources](docs/sources.md): the approved sources, exclusions and research findings
- [Reference library](docs/reference-library.md): reports and standards drafts can cite
- [Build timeline and decision log](docs/decisions.md): every build step in order, and the reasoning behind each decision

Built with Claude.
