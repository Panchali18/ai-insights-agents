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


def collect(sources: list, lookback_days: int) -> CollectionResult:
    """Read every source. A failing source is logged and skipped, never fatal."""
    result = CollectionResult()
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    seen_urls = set()

    for source in sources:
        name = source["name"]
        try:
            response = requests.get(
                source["url"], headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS
            )
            response.raise_for_status()
            feed = feedparser.parse(response.content)
            if not feed.entries:
                raise ValueError("feed returned no entries")
        except Exception as error:  # noqa: BLE001 - any failure just skips this source
            result.failed_sources.append((name, str(error)[:150]))
            continue

        kept = 0
        for entry in feed.entries:
            published = _entry_date(entry)
            if published and published < cutoff:
                continue
            url = entry.get("link", "")
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)
            result.items.append(
                Item(
                    id=len(result.items) + 1,
                    title=clean_text(entry.get("title", ""), 200),
                    source=name,
                    group=source.get("group", ""),
                    url=url,
                    published=published.strftime("%Y-%m-%d") if published else "unknown",
                    summary=clean_text(entry.get("summary", ""), 600),
                )
            )
            kept += 1
        result.ok_sources.append((name, kept))

    return result


def fetch_article_text(url: str, limit: int = 8000) -> str:
    """Fetch the full article page as plain text, to ground the draft. Returns '' on failure."""
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
    except Exception:  # noqa: BLE001
        return ""
    page = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", response.text)
    return clean_text(page, limit)
