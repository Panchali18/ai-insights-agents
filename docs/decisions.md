# Build timeline and decision log

Everything about how this project was built, in one place. The agent reads this file as source material for "building in public" posts (US-9.3), so it records only what has actually happened.

- **Build timeline:** each step in order, what was done and what happened. One line per step.
- **Decision log:** the detail behind each decision (why, alternatives, consequences). The timeline links to it by number (D1, D2…) instead of repeating it.

## Build timeline

| # | Date | What we did | What happened | Decision |
|---|---|---|---|---|
| 1 | 2026-10-10 | Defined the agent: research AI news and pain points, draft LinkedIn posts for human review | Agreed a six-point quality bar and the rule that the agent asks when unsure | D4 |
| 2 | 2026-10-10 | Chose how to build it | Code in a public repo, so the design is visible, over a chat-app configuration | D1 |
| 3 | 2026-10-10 | Checked the Claude API for free use | No starter credit on the account; AWS Bedrock access was still pending for another project | D2 |
| 4 | 2026-10-10 | Chose Gemini's free tier to run the agent, with Claude to build it | Model kept swappable in config | D2 |
| 5 | 2026-10-10 | Created the GitHub repo (public, MIT licence) | Repo live with README, licence and Python .gitignore | — |
| 6 | 2026-10-10 | Stored the Gemini key as a Codespaces secret | First attempt rejected: secret names allow only letters, numbers and underscores. Saved as `GEMINI_API_KEY` | — |
| 7 | 2026-10-10 | Wrote requirements v0.1 | 8 epics with user stories, acceptance criteria, guardrails and phases | — |
| 8 | 2026-10-10 | Researched sources and five comparable public agents | Found Reddit is ending its RSS feeds on 13 Nov 2026; approved 23 sources and a reference library | D5, D6 |
| 9 | 2026-10-10 | Set the run to produce 1 draft | Kept as a setting to raise later | D7 |
| 10 | 2026-10-10 | Built Phase 1: collect, rank, draft, save | Tested end to end with sample data and a stand-in model | — |
| 11 | 2026-10-10 | Confirmed GitHub budgets | $0 budgets with stop usage on every product, no payment method, so the project can't incur charges | — |
| 12 | 2026-10-10 | First dry run from the codespace | All 6 sources reachable; 73 items, 56 of them from the AI Incident Database | D8 |
| 13 | 2026-10-10 | First full run on `gemini-2.5-flash-lite` | Failed with "model not available", though the model was on the key's list: the error message was hiding the real cause | D9 |
| 14 | 2026-10-10 | Switched to `gemini-flash-latest` and ran again | First real draft: Azure document extraction. Reviewed at about 7/10; it relied on one vendor source and had AI-writing tells | D13 |
| 15 | 2026-10-10 | Stepped back on content strategy | Added four content pillars (Epic 9) and started this log | D10 |
| 16 | 2026-10-10 | Investigated why AI News returned 0 items | It stopped publishing after 10 Sep 2026; also found its feed is oldest-first, which exposed a bug in the per-source cap | D11 |
| 17 | 2026-10-10 | Added Hacker News as a second community source | 15 popular AI stories per run; AI News kept with a stale warning | D12 |
| 18 | 2026-10-10 | Ran with 47 items to rank | The ranking call appeared to hang; added a time limit and per-call timings | D14 |
| 19 | 2026-10-10 | Built Phase 2's critic-and-revise loop | Tested with sample data, including a critic that says "pass" while listing failures | D13 |
| 20 | 2026-10-10 | Saw the earlier ranking call's result | Google returned `504 DEADLINE_EXCEEDED` after silent retries; added a fallback model | D14 |
| 21 | 2026-10-10 | First real run of Phase 2 | Worked end to end. Picked "OpenAI withdraws three mathematical results"; the critic failed the first draft, it was revised once, then passed. 5 model calls, about 10 minutes in total, of which ranking took 319 seconds | D13 |
| 22 | 2026-10-10 | Reviewed run 21's draft by hand | The critic had passed it, but the only source was one post on X labelled "full article", the post stated inferences about OpenAI as fact, and AI-writing tells got through | D15 |
| 23 | 2026-10-13 | Made the critic stricter on framing and sources, and made the agent skip topics it can't read | Replaying run 21's draft: a lenient critic is now overruled and the draft is sent back | D15 |
| 24 | 2026-10-13 | Turned the author's writing rules into a style guide, with a code-level check | Run 21's draft fails on "highlights" and "serve as" | D16 |
| 25 | 2026-10-13 | Moved ranking to Flash-Lite | Pending a real run to measure the time saved | D17 |
| 26 | 2026-10-13 | Real run with the stricter critic | Ranking took 30 seconds on Flash-Lite (was 319). Topic: "The gap in shared understanding of LLM capability is widening", read as a social media post. The first draft call hit a 503 and the fallback model wrote it. The critic rejected the draft after 1 revision | D14, D15, D17 |
| 27 | 2026-10-13 | Reviewed run 26 | The draft was better (claims attributed, opinion marked) but rejected for minor style points. Bigger issue: the topic was a social media post, and most of the pool was vendor marketing, raw incident reports and engineer discussion | D18 |
| 28 | 2026-10-13 | Defined the audience | Hiring managers for AI roles, teams adopting AI, and BA and product peers. Not AI builders | D18 |
| 29 | 2026-10-13 | Reworked the source pool | Checked 11 more feeds; added 7 (analysis, product practice, enterprise, policy); excluded 4 with reasons; capped each group; ranking now scores for the audience | D18 |
| 30 | 2026-10-13 | Dry run with the new pool from the codespace | 22 items. The new business sources came through, but the 3 feeds on substack.com addresses were refused with 403 | D19 |
| 31 | 2026-10-13 | Moved Import AI and EU AI Act to the publishers' own sites; Epoch AI to reserve | Second dry run clean: 14 sources, no failures, 24 items. 10 of the 24 now come from analysis, product practice and enterprise sources, up from none | D19 |
| 32 | 2026-10-13 | Full run with the new pool | Pending | — |

---

# Decision log

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

## D14 · Fall back to a lighter model when Google's servers fail
**Date:** 2026-10-10 · **Phase:** 2

**Decision:** If the main model fails on Google's side (a 5xx error, overload or timeout), the agent retries once on a fallback model, `gemini-flash-lite-latest`. Errors caused by the request or the key (bad request, free-tier limit, unknown model) do not trigger the fallback. The library's own retries are limited to 2 attempts, and the ranking request sends shorter item summaries.

**Why:** A run ranking 47 items failed with `504 DEADLINE_EXCEEDED` after the library had silently retried the same model several times. The ranking call is the largest request the agent makes, and free-tier capacity varies.

**Alternatives considered:** Longer timeouts (slower failures, same outcome); splitting ranking into batches (more calls against the cap); switching the main model to Flash-Lite permanently (weaker judgement on every run).

**Consequence:** A busy main model costs one extra call instead of a failed run. The run output says when the fallback answered, so quality differences can be traced. Retrying only on server-side errors means a real mistake in the request still fails loudly.

---

## D15 · Check framing and source quality, and skip topics the agent can't read
**Date:** 2026-10-13 · **Phase:** 2

**Decision:** The critic now checks framing as well as facts: the writer's inference stated as fact, a number given a meaning the source doesn't give it, or criticism of a named company beyond what the source says (G4) all fail Q4. It flags single-source drafts and social media sources. Before drafting, the code reads the source page and labels honestly what it got (full article, social media post, blocked, too short); the label is passed to the drafter and critic. If a topic's page is blocked and the feed gave only a headline, the agent skips it and drafts the next-ranked topic, listing skipped topics in the drafts file.

**Why:** Run 21's draft passed the critic but wouldn't have been safe to post (timeline row 22). The critic checked that numbers appeared in the source, not whether the post drew fair conclusions from them, and it saw the same thin material as the writer. The draft was labelled "full article" though the source was a post on X, which mostly blocks automated readers.

**Alternatives considered:** Drafting from the headline with a warning (invites invented detail); finding a second source automatically (more calls and a search step; possible later).

**Consequence:** Ranking now returns 3 spare topics. Some weeks may produce no draft if no top topic is readable, which the file says plainly. A social media source can still be used, but the draft must attribute claims and ask the author to confirm them.

---

## D16 · Use the author's writing rules as the style guide, and check the clear-cut ones in code
**Date:** 2026-10-13 · **Phase:** 2 (brings forward part of Phase 3)

**Decision:** The author's writing rules are condensed into `prompts/style-guide.md`, given to both the drafter and the critic. Clear-cut breaks (banned words and phrases, em dashes, "it's not X, it's Y" reframes, bold inside the post, a closing question) are found by plain code in `agent/style.py`. If code finds any, Q6 fails whatever the critic says, and the breaks are added to the revision instructions.

**Why:** Run 21's critic passed "highlights" and "serve as", both on the author's banned list. A model reviewer is inconsistent on word lists; a code check isn't, and costs nothing.

**Consequence:** Resolves open question 4 in the requirements. The code check is deliberately narrow, so it rarely flags ordinary sentences; tone, analogies and subtler pivots stay with the critic.

---

## D17 · Rank with Flash-Lite, draft and critique with the main model
**Date:** 2026-10-13 · **Phase:** 2

**Decision:** The ranking call uses `gemini-flash-lite-latest` (`model.ranking_name` in config). Drafting and critiquing stay on the main model.

**Why:** Ranking took 319 seconds in run 21, about half the run. Scoring 47 headlines needs less judgement than writing or reviewing a post.

**Consequence:** Expected to cut run time substantially; to be measured on the next real run. If ranking quality drops (for example, case studies winning again), switch it back with one config line.

---

## D18 · Write for 3 business audiences and rebalance the source pool by group
**Date:** 2026-10-13 · **Phase:** 2

**Decision:** Posts are written for hiring managers for AI roles, teams adopting AI, and business analysts and product owners. The source pool is reorganised into groups, each with a cap on items per run. Added: One Useful Thing, AI as Normal Technology, Import AI, Epoch AI (Analysis); SVPG and The Product Compass (Product practice); McKinsey Insights filtered to AI articles (Enterprise); EU AI Act Newsletter (Policy). OpenAI, Hacker News and the AI Incident Database are cut to 5 items each, and Hacker News needs 100 points instead of 50. The ranking prompt scores topics on whether one of these readers could act on a post about them.

**Why:** Run 26 picked a social media post about LLM capability. The draft was accurate, but most of it summarised someone else's post. About 40 of 42 items in the pool came from vendor marketing, raw incident reports and engineer discussion, so ranking could only pick the best of a poor fit. A post adds value on LinkedIn when the author can say what a development means for a business, and the pool had few sources written for that reader.

**Alternatives considered:** Keeping the pool and tightening ranking only (it can't pick what isn't there); adding many more sources (more noise without caps); a Dynamics 365 group (deferred by the author).

**Consequence:** Newsletters post every 1 to 2 weeks, so they use a 14-day window. Many include the whole article in the feed, which the agent now uses when a page can't be read. 11 approved sources are in reserve, mostly written for AI builders. Stanford HAI is first in line once a page reader exists. Resolves open questions 2 and 8 in the requirements.

---

## D19 · Use publishers' own sites when substack.com refuses cloud servers
**Date:** 2026-10-13 · **Phase:** 2

**Decision:** Import AI is read from the author's own site (`jack-clark.net/feed/`). The EU AI Act source switches to the publisher's own site (`artificialintelligenceact.eu/feed/`), which carries in-depth explainers about monthly instead of the weekly newsletter. Epoch AI moves to reserve.

**Why:** In the first dry run from the codespace, all 3 feeds on `*.substack.com` addresses returned 403 Forbidden, while 2 Substack newsletters on their own domains worked and the same 3 feeds opened from another network. Substack appears to refuse automated requests from cloud servers to its own addresses. GitHub Actions also runs on cloud servers, so the weekly automation would hit the same block.

**Alternatives considered:** Sending a browser-like user agent to get past the block (rejected: it works around the site's own rule, against the handling rules in sources.md); a third-party feed proxy (another dependency that can fail).

**Consequence:** The weekly EU AI Act newsletter is lost, but the explainers suit practical posts. Future Substack sources need a check for a non-substack.com address first.

---

## Open issues

- **Quality gate and content direction changes agreed on 13 Oct 2026, not yet made:** split critic findings into major (block) and minor (list as quick fixes); make every draft postable as written, with personal touches as optional suggestions and "must check" questions only for unverified facts; full drafts from the build logs of both projects; news and research as short briefs where the author picks an angle.

- **The critic passed a draft it should have flagged** (run 21). Fixes made on 13 Oct 2026 (D15, D16, D17); confirm with a real run.

- **AI News (smol.ai) has published nothing since 10 Sep 2026** (see D11). Kept on the list; Hacker News added alongside it (D12).
- **The first draft relied on a single vendor source** (Microsoft writing about its own products). Phase 2 should flag single-vendor drafts and look for an independent view.
