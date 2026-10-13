# Sources

**Status:** v2.0 · **Last updated:** 2026-10-13

The sources the agent reads each week, how it reads each one, and why others were left out. The agent reads only sources in `config.yaml` (requirement US-1.1, AC1), and a source is added there only after its feed is checked.

**Audience** (decided 13 Oct 2026, [D18](decisions.md)): hiring managers for AI roles, teams adopting AI, and business analysts and product owners. AI researchers and engineers aren't the target, so sources written mainly for them are kept in reserve.

## Active sources (15)

Each group contributes at most a set number of items per run (`group_caps` in config), so the pool leans towards the groups that suit the audience. ✅ = feed checked and working on the date shown.

| Group (cap) | Source | Address | Status |
|---|---|---|---|
| Labs and vendors (6) | OpenAI news (max 5) | https://openai.com/news/rss.xml | ✅ 10 Oct |
| | Google DeepMind blog | https://deepmind.google/blog/feed | ✅ 10 Oct |
| | Microsoft Foundry blog | https://devblogs.microsoft.com/foundry/feed/ | ✅ 10 Oct |
| Community (8) | AI News (smol.ai) | https://news.smol.ai/rss.xml | ⚠️ No issue since 10 Sep 2026 ([D11](decisions.md)) |
| | Hacker News: AI stories with 100+ points (max 5) | https://hn.algolia.com/api/v1/search_by_date | ✅ 10 Oct ([D12](decisions.md)) |
| | AI Incident Database (max 5) | https://incidentdatabase.ai/rss.xml | ✅ 10 Oct |
| Analysis (10) | One Useful Thing (Ethan Mollick, Wharton) | https://www.oneusefulthing.org/feed | ✅ 13 Oct, full text in feed |
| | AI as Normal Technology (Princeton) | https://www.normaltech.ai/feed | ✅ 13 Oct, full text in feed |
| | Import AI (weekly) | https://importai.substack.com/feed | ✅ 13 Oct, full text in feed |
| | Epoch AI | https://epochai.substack.com/feed | ✅ 13 Oct, full text in feed |
| Product practice (8) | SVPG (Marty Cagan): product roles and AI | https://www.svpg.com/feed/ | ✅ 13 Oct, excerpts in feed |
| | The Product Compass: hands-on AI and product management | https://www.productcompass.pm/feed | ✅ 13 Oct, full text in feed |
| Enterprise (5) | McKinsey Insights, filtered to AI articles | https://www.mckinsey.com/insights/rss | ✅ 13 Oct, excerpts in feed |
| Policy (4) | EU AI Act Newsletter | https://artificialintelligenceact.substack.com/feed | ✅ 13 Oct, full text in feed |
| Research (3) | Carnegie Mellon ML blog (about monthly) | https://blog.ml.cmu.edu/feed/ | ✅ 10 Oct |

Newsletters post every 1 to 2 weeks, so they use a 14-day window instead of the default 7 days.

## In reserve

Approved on 10 Oct 2026 but not active, either because they're written mainly for AI builders or because they have no feed and need a page reader, which isn't built yet.

| Source | Address | Reason not active |
|---|---|---|
| Anthropic news | https://www.anthropic.com/news | No feed; needs a page reader |
| Stanford HAI | https://hai.stanford.edu/news | No feed; needs a page reader. Strong fit for the audience, so first in line |
| OWASP GenAI Security Project | https://genai.owasp.org | No feed; its standards are in the [reference library](reference-library.md) |
| Hamel Husain: LLM evaluation | https://hamel.dev | No feed; builder audience |
| Microsoft 365 Copilot Tech Community blog | https://techcommunity.microsoft.com/plugins/custom/microsoft/o365/custom-blog-rss?tid=-5888262158242517104&board=Microsoft365CopilotBlog&size=25 | Not yet tested |
| Google Research blog | https://research.google/blog/rss/ | Builder and research audience |
| Hugging Face blog | https://huggingface.co/blog/feed.xml | Builder audience |
| AWS Machine Learning blog | https://aws.amazon.com/blogs/machine-learning/feed/ | Builder audience |
| Simon Willison's weblog | https://simonwillison.net/atom/everything/ | Builder audience |
| Latent Space | https://www.latent.space/feed | Builder audience |
| Berkeley AI Research (BAIR) blog | https://bair.berkeley.edu/blog/feed.xml | Research audience |

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
| MIT Sloan Management Review | Strong fit, but its site disallows automated readers (robots.txt), and the agent respects that. Checked 13 Oct 2026. |
| Mind the Product | Its feed address returns a non-standard data format with no dates. Checked 13 Oct 2026; revisit if a standard feed appears. |
| Product Growth (Aakash Gupta) | Feed items are paywalled previews. Checked 13 Oct 2026. |
| Microsoft WorkLab | No feed. Its annual Work Trend Index is in the [reference library](reference-library.md). Checked 13 Oct 2026. |
| Microsoft Dynamics 365 and Copilot business apps | Deferred by decision on 13 Oct 2026; revisit later. |
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
