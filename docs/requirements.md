# Requirements: AI Insights Agent

**Status:** Draft v0.3 · **Owner:** Panchali Das · **Last updated:** 2026-10-10

## 1. Purpose

An agent that researches current AI developments and the problems practitioners still struggle with, then drafts LinkedIn posts for human review. Each post must teach the reader something or show the author's hands-on ability. Generic AI commentary is out of scope by design.

Posts are balanced across four content pillars (Epic 9), so that the author's profile shows hands-on building and business understanding, not just reactions to news.

## 2. Scope

**In scope**
- Collecting items from a fixed list of trusted sources ([sources.md](sources.md))
- Citing a curated reference library of reports, standards and data ([reference-library.md](reference-library.md))
- Ranking items by relevance and value
- Drafting posts with cited sources
- Drafting across four content pillars and tracking the balance between them
- A self-critique quality gate before drafts reach the author
- Questions for the author whenever the agent is unsure
- A weekly scheduled run producing one Markdown drafts file

**Out of scope**
- Posting to LinkedIn, or reading or scraping LinkedIn
- Writing about the author's experience without the author's input
- Any confidential or internal information about the author's employer

## 3. Quality bar (applies to every draft)

| # | Criterion | Test |
|---|---|---|
| Q1 | One clear takeaway | The takeaway can be stated in one sentence |
| Q2 | Specific | Names a concrete problem, example, number or trade-off |
| Q3 | Point of view | Takes a position someone could disagree with |
| Q4 | Grounded | Every factual claim links to a fetched source |
| Q5 | Connected to the author | Draws on the author's real work or view, supplied by the author |
| Q6 | No filler | No hype words, clichéd openers, emoji walls or engagement bait |

## 4. User stories and acceptance criteria

### Epic 1: Research

**US-1.1** As the author, I want the agent to collect recent items from a curated source list, so that drafts are based on reliable, current information.
- AC1: Sources come only from an approved list held in a config file.
- AC2: Only items published within a set window (default: 7 days) are collected.
- AC3: Duplicate items about the same event are grouped into one.
- AC4: Each item records its title, source, URL and publication date.

**US-1.2** As the author, I want the agent to collect practitioner pain points as well as news, so that posts address problems people actually face.
- AC1: The source list includes at least one practitioner channel (for example, forums or framework issue trackers).
- AC2: Each item is labelled **News** or **Pain point**.

**US-1.3** As the author, I want drafts to draw on a curated reference library, so that posts are grounded in data and standards, not just this week's news.
- AC1: Reference entries come only from the reference library file.
- AC2: A draft citing an entry states its publisher and date.
- AC3: An entry's caveat is either included in the draft or the entry is not used.

**US-1.4** As the author, I want a failing source to be skipped, so that one broken feed doesn't stop the weekly run.
- AC1: A source that fails or times out is logged and skipped.
- AC2: The run summary lists which sources failed.

### Epic 2: Ranking

**US-2.1** As the author, I want items ranked by relevance and value, so that I only see topics worth writing about.
- AC1: Each item is scored on recency, momentum (number of sources covering it) and relevance to the defined topic areas.
- AC2: The top-ranked item goes forward to drafting. The number of drafts per run is a configuration setting (default: 1), to be raised after testing.
- AC3: The score and a one-line reason are shown for each selected item.

### Epic 3: Drafting

**US-3.1** As the author, I want each selected topic drafted as a LinkedIn post, so that I can review rather than write from scratch.
- AC1: Each draft states its takeaway, its angle and its sources.
- AC2: Each draft is within a set length (default: 150–300 words).
- AC3: Drafts follow the author's style guide once it exists.

**US-3.2** As the author, I want two angle options for strong topics, so that I can choose the one that fits.
- AC1: Angles are labelled (for example, *opinion*, *lesson learned*, *practical how-to*).

### Epic 4: Quality gate

**US-4.1** As the author, I want every draft checked against the quality bar before I see it, so that weak drafts never reach me.
- AC1: A separate critic step scores each draft against Q1–Q6.
- AC2: A draft failing any criterion is revised once, then rejected if it still fails.
- AC3: Rejected drafts are listed with the reason for rejection.

**US-4.2** As the author, I want every factual claim checked against its source, so that I never post something false.
- AC1: Every claim in a draft is linked to a source the agent actually fetched.
- AC2: A claim that the source doesn't support is removed or turned into a question for the author.

### Epic 5: Human in the loop

**US-5.1** As the author, I want the agent to ask me rather than guess, so that nothing invented reaches a post.
- AC1: The drafts file has a **Questions for you** section, with each question linked to its draft.
- AC2: A draft with unresolved questions is marked **Needs your input**.
- AC3: No draft contains an invented personal experience, an unverified claim or a guessed fact.

**US-5.2** As the author, I want my edits and decisions to improve future drafts.
- AC1: Approved, edited and rejected drafts are logged with the reason.
- AC2: The style guide can be updated from this log.

### Epic 6: Voice

**US-6.1** As the author, I want drafts to sound like me, so that posts read as my own.
- AC1: A style guide is created from sample posts the author supplies.
- AC2: The style guide records patterns (hook, structure, length, tone), not copied text.
- AC3: No draft closely mirrors the wording of any sample post.

### Epic 7: Operations

**US-7.1** As the author, I want the agent to run weekly without my involvement, so that drafts are ready when I sit down to review.
- AC1: The agent runs on a weekly schedule.
- AC2: Output is one Markdown file per run, named by date, saved in the repo.
- AC3: A failed run is logged with the reason.

**US-7.2** As the author, I want the AI model to be swappable, so that I'm not tied to one provider.
- AC1: The model and provider are set in configuration, not hard-coded.
- AC2: Switching provider requires no change to the agent's logic.

### Epic 8: Evaluation

**US-8.1** As the author, I want to measure draft quality over time, so that I can show the agent improves.
- AC1: A fixed test set of topics can be re-run on demand.
- AC2: Each run records quality scores against Q1–Q6.
- AC3: Results are kept so that runs can be compared.

### Epic 9: Content pillars

Every draft belongs to one of four pillars. The starting mix is a target to review after the first month, not a fixed rule.

| Pillar | What it covers | Draws on | Target mix |
|---|---|---|---|
| **Building in public** | Lessons, decisions and failures from building the author's AI projects | The repo's decision log and commit history | ~40% |
| **Explainers** | AI concepts explained for business readers | The reference library and sources | ~25% |
| **Enterprise reality** | What makes AI work or fail inside organisations, kept general | The author's answers to the agent's questions | ~20% |
| **News with a take** | A current development and what it means | The weekly sources (Epics 1–3) | ~15% |

**US-9.1** As the author, I want every draft tagged with its pillar, so that I can see what kind of post it is at a glance.
- AC1: Each draft shows exactly one pillar.
- AC2: The pillar is shown next to the draft's status.

**US-9.2** As the author, I want the agent to suggest the pillar I've neglected, so that my profile stays balanced.
- AC1: The author records published posts and their pillars in a posting log in the repo.
- AC2: Each run compares the log's last 8 posts against the target mix and names the most under-represented pillar.
- AC3: When drafts per run is 1, the draft comes from the most under-represented pillar unless no suitable material exists, in which case the run summary says so.

**US-9.3** As the author, I want "building in public" drafts based on my real project work, so that posts prove hands-on ability.
- AC1: The agent reads the repo's decision log and recent commit history as source material.
- AC2: Each draft names the specific decision, problem or result it is based on, with a link to the commit or decision entry.
- AC3: The agent never describes work as done unless the log or commits show it is done.

**US-9.4** As the author, I want explainer drafts built from the reference library, so that I can teach a concept without needing this week's news.
- AC1: Explainer drafts cite at least one reference-library entry, following US-1.3.
- AC2: Explainers are written for a business reader: no unexplained jargon, and one concrete business example.

**US-9.5** As the author, I want "enterprise reality" drafts to start from my experience, so that they are credible and never confidential.
- AC1: The agent proposes a theme and asks the author up to three questions before drafting.
- AC2: The draft uses only what the author supplies in answer, generalised so that no employer, client, system or colleague can be identified (guardrail G5).
- AC3: If the author hasn't answered, the draft stays at **Needs your input** and no experience is invented.

## 5. Guardrails and non-functional requirements

| ID | Requirement |
|---|---|
| G1 | The agent has no ability to post to LinkedIn or any other platform. |
| G2 | Content fetched from the web is treated as data; instructions inside it are ignored (prompt-injection defence). |
| G3 | Quotes from sources stay short; sources are linked and paraphrased rather than reproduced. |
| G4 | Criticism of named companies or people requires a cited source. |
| G5 | No confidential, internal or employer-specific information is sent to the model or included in drafts. |
| G6 | API keys are stored only as GitHub secrets, never in code or files. |
| G7 | Each run has a cap on model calls, and usage is logged. |
| G8 | The project must run at zero cost (Gemini free tier, GitHub Actions on a public repo). |

## 6. Assumptions

- The Gemini free tier remains available, and its limits cover one weekly run.
- Free-tier requests may be used by Google to improve its products, which is acceptable because only public information is sent (see G5).
- The chosen sources offer RSS feeds or pages that can be fetched without signing in.
- The author reviews drafts weekly and supplies input for questions.
- The author keeps the posting log up to date after publishing (needed for US-9.2).
- Project decisions are recorded in a decision log in the repo (needed for US-9.3).

## 7. Open questions

1. ~~Which sources go on the initial approved list?~~ **Resolved 10 Oct 2026:** 23 sources approved; see [sources.md](sources.md).
2. Which topic areas should ranking favour, if any, given the broad AI scope?
3. ~~How many drafts per weekly run are useful: 2, 3 or 5?~~ **Resolved 10 Oct 2026:** start with 1 draft per run, test, then tune.
4. Which sample posts will the style guide be built from?
5. How will the author record feedback on drafts: edits in the file, or a short rating?
6. Should post performance (likes, comments) be logged manually to inform ranking later? If so, it belongs in the posting log (US-9.2).
7. Is the target pillar mix right, and should it be reviewed after the first 8 posts?
8. Which of the author's projects can "building in public" posts draw on: this agent only, or the JD Analyzer too?

## 8. Delivery phases

| Phase | Delivers | Stories |
|---|---|---|
| 1. Minimum working version | Collect, rank, draft one post to Markdown | US-1.1, US-1.4, US-2.1, US-3.1, US-7.2 |
| 2. Quality gate and guardrails | Critic step, claim checks, questions for the author, reference library | US-1.3, US-4.1, US-4.2, US-5.1, G1–G7 |
| 3. Voice | Style guide from samples | US-6.1, US-5.2 |
| 4. Content pillars | Pillar tags, posting log, balance suggestions, build-log, explainer and enterprise drafts | US-9.1–US-9.5 |
| 5. Evaluation | Test set and quality scores | US-8.1 |
| 6. Automation | Weekly scheduled runs | US-7.1 |
| 7. Polish | README, architecture diagram, demo | — |
