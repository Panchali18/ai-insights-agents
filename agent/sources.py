"""Collect recent items from the approved sources (US-1.1, US-1.4)."""

import html
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import feedparser
import requests

USER_AGENT = "ai-insights-agent/0.1 (+https://github.com/Panchali18/ai-insights-agents)"
TIMEOUT_SECONDS = 20


@dataclass
class Item:
    id: int
    title: str
    source: str
    group: str
    url: str
    published: str
    summary: str


@dataclass
class CollectionResult:
    items: list = field(default_factory=list)
    ok_sources: list = field(default_factory=list)
    failed_sources: list = field(default_factory=list)  # (name, reason)
    stale_sources: list = field(default_factory=list)  # (name, date of newest item)


def clean_text(raw: str, limit: int) -> str:
    """Strip HTML tags and extra whitespace, then trim to a length limit."""
    text = re.sub(r"<[^>]+>", " ", raw or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]


def _entry_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        value = entry.get(key)
        if value:
            return datetime(*value[:6], tzinfo=timezone.utc)
    return None


def collect(
    sources: list, lookback_days: int, max_per_source: int = 15, stale_after_days: int = 21
) -> CollectionResult:
    """Read every source. A failing source is logged and skipped, never fatal.
    Each source contributes at most max_per_source items (newest first), so one busy feed
    can't crowd out the rest. A source whose newest item is older than stale_after_days is
    flagged as stale: it is reachable but appears to have stopped publishing."""
    result = CollectionResult()
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=lookback_days)
    oldest = datetime.min.replace(tzinfo=timezone.utc)
    seen_urls = set()

    for source in sources:
        name = source["name"]
        try:
            if source.get("type") == "hn_search":
                entries = _hn_entries(source, cutoff)  # already sorted, most discussed first
            else:
                entries = _rss_entries(source)
                if not entries:
                    raise ValueError("feed returned no entries")
                # Feeds don't all list newest first, so sort by date before applying the cap.
                entries.sort(key=lambda e: e["published"] or oldest, reverse=True)
                newest = entries[0]["published"]
                stale_days = source.get("stale_after_days", stale_after_days)
                if newest and newest < now - timedelta(days=stale_days):
                    result.stale_sources.append((name, newest.strftime("%Y-%m-%d")))
        except Exception as error:  # noqa: BLE001 - any failure just skips this source
            result.failed_sources.append((name, str(error)[:150]))
            continue

        kept = 0
        for entry in entries:
            if kept >= max_per_source:
                break
            published = entry["published"]
            if published and published < cutoff:
                continue
            url = entry["link"]
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            result.items.append(
                Item(
                    id=len(result.items) + 1,
                    title=clean_text(entry["title"], 200),
                    source=name,
                    group=source.get("group", ""),
                    url=url,
                    published=published.strftime("%Y-%m-%d") if published else "unknown",
                    summary=clean_text(entry["summary"], 600),
                )
            )
            kept += 1
        result.ok_sources.append((name, kept))

    return result


def _rss_entries(source: dict) -> list:
    """Read an RSS or Atom feed into plain entry dicts."""
    response = requests.get(source["url"], headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    return [
        {
            "title": e.get("title", ""),
            "link": e.get("link", ""),
            "published": _entry_date(e),
            "summary": e.get("summary", ""),
        }
        for e in feed.entries
    ]


HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


def _hn_entries(source: dict, cutoff: datetime) -> list:
    """Search Hacker News (free Algolia API, no key) for recent, popular stories matching any of
    the source's queries. Returns them sorted by discussion size, so the cap keeps the stories
    practitioners talked about most."""
    min_points = source.get("min_points", 50)
    found = {}
    for query in source["queries"]:
        response = requests.get(
            HN_SEARCH_URL,
            params={
                "query": query,
                "tags": "story",
                "numericFilters": f"created_at_i>{int(cutoff.timestamp())},points>={min_points}",
                "hitsPerPage": 50,
            },
            headers={"User-Agent": USER_AGENT},
            timeout=TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        for hit in response.json().get("hits", []):
            found[hit["objectID"]] = hit

    entries = []
    for hit in sorted(found.values(), key=lambda h: (h.get("num_comments") or 0), reverse=True):
        discussion = f"https://news.ycombinator.com/item?id={hit['objectID']}"
        published = datetime.fromtimestamp(hit["created_at_i"], tz=timezone.utc)
        entries.append(
            {
                "title": hit.get("title") or "",
                "link": hit.get("url") or discussion,  # Ask HN posts have no external link
                "published": published,
                "summary": (
                    f"Hacker News story with {hit.get('points', 0)} points and "
                    f"{hit.get('num_comments', 0)} comments. Discussion: {discussion}"
                ),
            }
        )
    return entries


SOCIAL_DOMAINS = (
    "x.com", "twitter.com", "linkedin.com", "facebook.com", "instagram.com",
    "threads.net", "bsky.app", "reddit.com", "youtube.com", "tiktok.com",
)
BLOCK_MARKERS = (
    "javascript is not available", "enable javascript", "please enable js", "sign in to",
    "log in to", "login required", "create an account to", "subscribe to continue",
    "subscribe to read", "access denied", "verify you are human", "are you a robot", "captcha",
)
MIN_ARTICLE_CHARS = 1500


@dataclass
class Article:
    text: str
    kind: str  # "full article" | "social media post" | "blocked" | "too short" | "unreachable"

    @property
    def usable(self) -> bool:
        return self.kind in ("full article", "social media post")


def _is_social(url: str) -> bool:
    host = re.sub(r"^https?://(www\.|mobile\.)?", "", url.lower()).split("/")[0]
    return any(host == d or host.endswith("." + d) for d in SOCIAL_DOMAINS)


def fetch_article(url: str, limit: int = 8000) -> Article:
    """Fetch the source page and say honestly what came back, so drafts aren't labelled
    'full article' when the agent only saw a login wall or a fragment."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception:  # noqa: BLE001
        return Article("", "unreachable")
    page = re.sub(r"(?is)<(script|style|nav|footer|header|noscript)[^>]*>.*?</\1>", " ", response.text)
    text = clean_text(page, limit)
    head = text[:3000].lower()
    if any(marker in head for marker in BLOCK_MARKERS):
        return Article(text, "blocked")
    if _is_social(url):
        return Article(text, "social media post")
    if len(text) < MIN_ARTICLE_CHARS:
        return Article(text, "too short")
    return Article(text, "full article")
