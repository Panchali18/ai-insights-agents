# Sources

**Status:** Approved v1.0 · **Last updated:** 2026-10-10

The approved list of sources the agent reads each week, how it reads each one, and why other sources were left out. The agent reads only sources on this list (requirement US-1.1, AC1).

**Status key**
- ✅ Feed checked and working on 10 Oct 2026
- 📋 Listed in a reliable feed directory or on the publisher's site; to be tested during the build
- ⚠️ No feed; the agent reads the web page directly. These are the fragile sources, because a site redesign can break them.

## Approved sources (23)

### Labs and vendors (6)

| Source | Access | Address | Status |
|---|---|---|---|
| OpenAI news | RSS | https://openai.com/news/rss.xml | ✅ |
| Google DeepMind blog | RSS | https://deepmind.google/blog/feed | ✅ |
| Anthropic news | Page read | https://www.anthropic.com/news | ⚠️ |
| Google Research blog | RSS | https://research.google/blog/rss/ | 📋 |
| Hugging Face blog | RSS | https://huggingface.co/blog/feed.xml | 📋 |
| AWS Machine Learning blog | RSS | https://aws.amazon.com/blogs/machine-learning/feed/ | 📋 |

### Microsoft (2)

| Source | Access | Address | Status |
|---|---|---|---|
| Microsoft Foundry blog | RSS | https://devblogs.microsoft.com/foundry/feed/ | ✅ (feed link on site; latest post 7 Oct 2026) |
| Microsoft 365 Copilot Tech Community blog | RSS | https://techcommunity.microsoft.com/plugins/custom/microsoft/o365/custom-blog-rss?tid=-5888262158242517104&board=Microsoft365CopilotBlog&size=25 | 📋 |

### Community and practitioner pain points (5)

| Source | Access | Address | Status |
|---|---|---|---|
| AI News (smol.ai): summarises top AI Discord servers, subreddits and X accounts | RSS | https://news.smol.ai/rss.xml | ✅ |
| Hacker News: high-scoring AI posts | Free search API | https://hn.algolia.com/api/v1/search | 📋 |
| Simon Willison's weblog | Atom | https://simonwillison.net/atom/everything/ | 📋 |
| Hamel Husain: LLM evaluation | Page read | https://hamel.dev | ⚠️ |
| AI Incident Database: real-world AI failures | RSS | https://incidentdatabase.ai/rss.xml | ✅ (feed link on site) |

### Analysis and critical voices (5)

| Source | Access | Address | Status |
|---|---|---|---|
| Latent Space: AI engineering | Newsletter feed | https://www.latent.space/feed | 📋 |
| Import AI: research and policy, weekly | Newsletter feed | https://importai.substack.com/feed | 📋 |
| Epoch AI, Gradient Updates: one in-depth question a week | Newsletter feed | https://epochai.substack.com/feed | 📋 |
| AI as Normal Technology (Princeton, formerly *AI Snake Oil*) | Newsletter feed | https://www.normaltech.ai/feed | 📋 |
| One Useful Thing (Ethan Mollick, Wharton) | Newsletter feed | https://www.oneusefulthing.org/feed | 📋 |

### Research institutions (3)

| Source | Access | Address | Status |
|---|---|---|---|
| Stanford HAI: research, policy, AI Index | Page read | https://hai.stanford.edu/news | ⚠️ |
| Carnegie Mellon ML blog: about monthly | RSS | https://blog.ml.cmu.edu/feed/ | ✅ (feed link on site) |
| Berkeley AI Research (BAIR) blog | RSS | https://bair.berkeley.edu/blog/feed.xml | 📋 |

### Policy and security (2)

| Source | Access | Address | Status |
|---|---|---|---|
| EU AI Act Newsletter | Newsletter feed | https://artificialintelligenceact.substack.com/feed | 📋 |
| OWASP GenAI Security Project | Page read | https://genai.owasp.org | ⚠️ |

## Handling rules

- **A failing source never fails the run.** The agent logs the failure and continues with the other sources.
- **Page-read sources are read politely:** once per run, respecting each site's robots.txt.
- **Fetched content is data, not instructions** (guardrail G2).
- **Academic blogs post monthly at best**, so they will rarely appear in a weekly run. Their value is depth, not news.

## Excluded sources and why

| Source | Reason |
|---|---|
| Reddit | Reddit announced it will discontinue its RSS feeds on 13 Nov 2026, and it already blocks many automated and datacenter clients, which is where GitHub Actions runs from. Covered indirectly by AI News (smol.ai). |
| X (Twitter) and Discord | Need accounts and risk breaking terms of service. Covered indirectly by AI News (smol.ai). |
| arXiv | Hundreds of papers a day; too noisy for a weekly run. Important papers surface through Import AI, Epoch AI and AI News. |
| Microsoft AI blog and Microsoft AI news | The blog feed no longer exists; the news page has not posted in over a year. Replaced by the Foundry and M365 Copilot blogs. |
| Copilot Studio | No dedicated feed found. Its updates appear in the two Microsoft sources above. |
| General tech news (TechCrunch, The Verge) | Mostly repeat what the lab blogs announce. |
| MIT News: AI | Overlaps with the other research sources. |
| Columbia University | No feed; its AI news page mostly collects press coverage rather than research. |
| ADAPT Centre (Ireland) | No feed; left out by decision on 10 Oct 2026. |
| AI Ireland | Newsroom last updated Nov 2025; no feed. |
| MBZUAI (UAE) | No direct feed found. Revisit if UAE coverage becomes a priority. |
| Lenny's Newsletter, Stratechery | Paywalled: the agent can't read them, and reusing their content raises copyright issues. |
| Artificial Analysis | Valuable benchmark data but no feed. Kept in the [reference library](reference-library.md) instead. |

## Research findings

How comparable public agents source their data (researched 10 Oct 2026):

- **[AI News by smol.ai](https://news.smol.ai/)** summarises top AI Discord servers, subreddits and X accounts into weekday recaps for over 150,000 engineers. It doesn't publish exactly which ones.
- **[Auto-News](https://github.com/finaldie/auto-news)** (open source) pulls from X, RSS, YouTube, web articles and Reddit, filters by personal interest, and produces a weekly top-k recap. It supports several models, including Gemini.
- **[An n8n newsletter workflow](https://n8n.io/workflows/12533-curate-and-generate-an-ai-newsletter-from-rss-feeds-with-openai-and-slack/)** uses 15+ sources, keeps the top 4 stories, drafts a newsletter, and sends it to Slack for human approval and revision. It is the closest match to this agent's design and confirms the human-review step is standard practice.
- **[ai-news-aggregator](https://www.sourcepulse.org/projects/29992358)** uses 140+ sources but only filters by keyword, with no ranking or summarising. More sources without ranking just means more noise.
- **[allainews_sources](https://www.sourcepulse.org/projects/1833839)** is a curated list of AI feeds, several of them now broken. Feeds decay, so the agent must handle dead sources gracefully.

**Design implications**
1. Combine three kinds of source (labs, community, analysis), as the comparable agents do.
2. Rank, don't just filter. A small, ranked set beats a large, filtered one.
3. Use an aggregator (smol.ai) for community signal instead of reading Reddit, Discord or X directly.
4. Expect feeds to break, and design for it.

**References:** [Feeder: AI news RSS feeds](https://feeder.co/knowledge-base/rss-content/ai-news-rss-feeds/) · [Open RSS: Reddit feed reliability](https://openrss.org/work/161) · [Reddit RSS vs API in 2026](https://www.redditapis.com/blogs/reddit-rss-feed-vs-api-2026) · [Institute of AI Product Management: AI PM newsletters](https://www.institutepm.com/knowledge-hub/best-ai-pm-newsletters)
