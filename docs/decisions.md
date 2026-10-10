# Decision log

Key project decisions, newest last. Each entry records what was decided, why, what else was considered, and what it changed. The agent reads this file as source material for "building in public" posts (US-9.3), so entries describe only what has actually happened.

---

## D1 · Build the agent in code, not as a chat-app configuration
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Build the agent as a Python project in a public GitHub repo, calling a model through its API.

**Why:** The project is a portfolio piece. A scheduled task inside a chat app would cost nothing extra, but it's configuration, and it can't show agent design, guardrails or evaluation.

**Alternatives considered:** A Claude app project with instructions and a scheduled task.

**Consequence:** More setup work, and every design choice is visible and reviewable in the repo.

---

## D2 · Build with Claude, run on Gemini's free tier, keep the model swappable
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Use Claude to design and write the code. The running agent calls Gemini through a Google AI Studio key. The provider and model are configuration settings.

**Why:** The project must run at zero cost (G8). The Claude API account had no starter credit, so it needed a US$5 prepaid top-up. AWS Bedrock was blocked on a model-access request for another project. Gemini's free tier needs no billing account, and going over its limits returns an error instead of a charge.

**Alternatives considered:** Claude API with US$5 credit; Claude on AWS Bedrock; Claude on Google Vertex AI or Microsoft Foundry (both need cloud billing setup).

**Consequence:** The project can't be described as "a Claude agent". Free-tier requests may be used by Google to improve its products, so only public information is sent (G5). Switching to Claude later needs a new provider adapter and some API credit.

---

## D3 · Write drafts to a Markdown file in the repo
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Each run saves one dated Markdown file in `drafts/`.

**Why:** It's the simplest output to build, review and version. A Google Doc would add an integration for little gain.

**Alternatives considered:** A Google Doc the author comments on.

**Consequence:** Reviewing happens in the repo or codespace. The draft can be pasted into a doc by hand if needed.

---

## D4 · The agent asks when unsure and can't post anywhere
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Anything the agent can't verify, or that needs the author's own experience, becomes a question for the author. The agent has no ability to post.

**Why:** Invented experience is the worst failure for a personal brand, and a risk in interviews. A human reviews every draft.

**Consequence:** Drafts with open questions are marked **Needs your input** (US-5.1). The first real draft did this correctly.

---

## D5 · Approve 23 sources; exclude Reddit, X and Discord
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Use the 23 sources in [sources.md](sources.md). Use AI News (smol.ai) for community signal instead of reading Reddit, X or Discord directly.

**Why:** Reddit announced it will discontinue its RSS feeds on 13 Nov 2026, and it already blocks many automated and datacenter clients. X and Discord need accounts and risk breaking terms of service. AI News already summarises top AI subreddits, Discord servers and X accounts.

**Alternatives considered:** Reddit RSS, the Reddit API, a third-party Reddit data service.

**Consequence:** Community coverage depends on one aggregator. If AI News stops publishing, the agent loses most of its community signal.

---

## D6 · Keep a reference library separate from the weekly feeds
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Reports, standards and benchmark data go in [reference-library.md](reference-library.md), with a caveats column, instead of being checked weekly.

**Why:** Material such as the OWASP Top 10 and the Stanford AI Index changes rarely, and posts are stronger when grounded in it.

**Consequence:** Contested figures, such as the widely quoted "95% of AI pilots fail", must carry their caveat or not be used.

---

## D7 · Start with 1 draft per run
**Date:** 2026-10-10 · **Phase:** 1

**Decision:** `drafts_per_run` defaults to 1.

**Why:** One draft makes problems easy to spot during testing. It's a setting, so it can be raised without code changes.

---

## D8 · Cap each source at 15 items
**Date:** 2026-10-10 · **Phase:** 1

**Decision:** Each source contributes at most 15 items per run (`max_items_per_source`).

**Why:** The first dry run collected 73 items, and 56 came from the AI Incident Database. One busy feed would have crowded out the lab and Microsoft sources in ranking.

**Consequence:** The second run ranked 32 items from a better mix.

---

## D9 · Use the `gemini-flash-latest` model alias, for now
**Date:** 2026-10-10 · **Phase:** 1

**Decision:** Use Google's alias for the current Flash model. Pin an exact version once a model is confirmed stable.

**Why:** The first model tried, `gemini-2.5-flash-lite`, failed. The error handler reported "model not available", but the model was in the key's model list, so the message was hiding the real cause. The handler now prints the underlying error, and a `--list-models` option shows which models the key can use.

**Consequence:** The alias can change underneath the agent, which makes evaluation results harder to compare run to run (Phase 5). Lesson: an error message that guesses the cause can cost more time than no message at all.

---

## D10 · Balance posts across four content pillars
**Date:** 2026-10-10 · **Phase:** Planning

**Decision:** Every draft belongs to one pillar: building in public (~40%), explainers (~25%), enterprise reality (~20%) or news with a take (~15%). See Epic 9 in the [requirements](requirements.md).

**Why:** A profile that was quiet and then posts only polished takes on AI news reads as performed expertise. Posts about real build work are the hardest to fake and give the sudden activity a clear reason.

**Consequence:** The agent needs this decision log, a posting log and the reference library as sources, alongside the weekly feeds.

---

## D11 · Sort feeds by date before capping, and warn on stale sources
**Date:** 2026-10-10 · **Phase:** 1

**Decision:** Sort each feed's entries newest first before applying the per-source cap. Flag any reachable source whose newest item is older than 21 days (configurable per source; 90 days for the Carnegie Mellon blog, which posts about monthly).

**Why:** AI News (smol.ai) returned 0 items in both runs. The feed worked; the newsletter's newest issue was dated 10 Sep 2026, a month earlier, and no pause had been announced. The investigation found two more problems: the feed lists issues oldest first, and two different issues shared an identical timestamp. With an oldest-first feed, the cap from D8 would have kept the oldest recent items and dropped the newest.

**Consequence:** A source that goes quiet now shows a ⚠ warning in the terminal and the run summary, instead of a silent 0. The community signal from D5 is weaker until AI News resumes or is replaced. Lesson: "0 items" can mean the code is broken, the source is broken, or the source has stopped; each needs a different fix, so the run should say which.

---

## D12 · Add Hacker News as a second community source, and keep AI News
**Date:** 2026-10-10 · **Phase:** 1

**Decision:** Add Hacker News through its free Algolia search API (no key). Each run searches for stories from the lookback window with at least 50 points, matching any of: LLM, AI agent, RAG, OpenAI, Anthropic, Gemini. Stories are ranked by number of comments before the per-source cap. AI News stays on the list.

**Why:** AI News went quiet (D11), leaving the agent with little community signal. Hacker News is very active and its discussions show what practitioners struggle with. Sorting by comments favours debated topics, which tend to be pain points, over simple announcements.

**Alternatives considered:** Waiting for AI News to resume; the hnrss.org feed service (a third-party wrapper around the same data).

**Consequence:** Hacker News items have no article summary, only the title, points and comment count, so ranking relies on the title. Ask HN posts link to the discussion itself. If AI News resumes, the stale warning (D11) disappears and both sources contribute.

---

## D13 · Add a critic-and-revise loop, and don't trust the critic's own verdict
**Date:** 2026-10-10 · **Phase:** 2

**Decision:** After drafting, a separate model call reviews the draft against the quality bar (Q1–Q6), checks each factual claim against the source, flags AI-writing tells and single-vendor sourcing, and returns a verdict. A failing draft is revised once with the critic's instructions and reviewed again. If it still fails, it is marked **Rejected** and kept in the file with the reasons. The code decides pass or fail from the critic's findings (every criterion passes and every claim is supported), not from its stated verdict.

**Why:** This is the first point where the model's output decides what the agent does next, which is what separates an agent from a fixed pipeline. The first real draft relied on one vendor source and had AI-writing tells (an em dash, "earns its keep") that a reviewer would have caught. Models sometimes report "pass" while listing failures, so the stated verdict alone can't be trusted.

**Alternatives considered:** The drafter checking its own work in the same call (cheaper, but it tends to approve itself); unlimited revision rounds (cost and time grow, and drafts drift away from the source).

**Consequence:** One draft now uses up to 5 model calls instead of 2, so the call cap rose from 5 to 8. A run takes longer. Rejected drafts stay visible, so the author can see the gate working rather than just getting fewer drafts. Output files no longer overwrite an earlier run from the same day.

---

## Open issues

- **AI News (smol.ai) has published nothing since 10 Sep 2026** (see D11). Kept on the list; Hacker News added alongside it (D12).
- **The first draft relied on a single vendor source** (Microsoft writing about its own products). Phase 2 should flag single-vendor drafts and look for an independent view.
