"""Helpers for fetching and normalizing RSS feed articles."""

from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
import re
import xml.etree.ElementTree as ET

import httpx

from .api_utils import format_source_from_url
from .article_models import ArticleOriginal

_TAG_RE = re.compile(r"<[^>]+>")
_DEFAULT_TIMEOUT = 10.0


class RSSFetchError(RuntimeError):
    """Raised when fetching or parsing an RSS feed fails."""


def _strip_markup(value: str | None) -> str:
    if not value:
        return ""
    without_tags = _TAG_RE.sub("", value)
    return unescape(without_tags)


def _parse_pub_date(pub_date_raw: str | None) -> datetime | None:
    if not pub_date_raw:
        return None
    try:
        parsed = parsedate_to_datetime(pub_date_raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def fetch_korea_herald_rss(*, limit: int | None = None) -> list[ArticleOriginal]:
    """Fetch and normalize articles from the Korea Herald K-pop RSS feed."""

    url = "https://www.koreaherald.com/rss/kh_Kpop"
    try:
        response = httpx.get(url, timeout=_DEFAULT_TIMEOUT)
        response.raise_for_status()
    except httpx.HTTPError as exc:  # pragma: no cover - network failures
        raise RSSFetchError(f"Failed to fetch Korea Herald RSS feed: {exc}") from exc

    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as exc:  # pragma: no cover - malformed feed
        raise RSSFetchError("Failed to parse Korea Herald RSS feed.") from exc

    channel = root.find("channel")
    if channel is None:
        raise RSSFetchError("Korea Herald RSS feed is missing a channel element.")

    articles: list[ArticleOriginal] = []
    for item in channel.findall("item"):
        if limit is not None and len(articles) >= limit:
            break

        link = item.findtext("link")
        title = _strip_markup(item.findtext("title"))
        description = _strip_markup(item.findtext("description"))
        pub_date = _parse_pub_date(item.findtext("pubDate"))

        if not link or not title or pub_date is None:
            continue

        source = format_source_from_url(link, fallback="Korea Herald")
        articles.append(
            ArticleOriginal(
                artist=None,
                original_url=link.strip(),
                title_original=title.strip(),
                description=description.strip(),
                published_at=pub_date,
                api="korea_herald_rss",
                category="news",
                source=source,
            )
        )

    return articles


__all__ = ["RSSFetchError", "fetch_korea_herald_rss"]
