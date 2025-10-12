"""Naver News API helpers returning normalized article records."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Mapping

import certifi

from .article_models import ArticleOriginal
from .naver_client import request_items, strip_markup
from .api_utils import format_source_from_url

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class NaverNewsApiError(RuntimeError):
    """Raised when a Naver news API request fails."""


def _parse_pub_date(pub_date_raw: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(pub_date_raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def fetch_naver_news(
    query: str,
    *,
    artist: str,
    display: int = 30,
    sort: str | None = "date",
) -> list[ArticleOriginal]:
    params: dict[str, Any] = {"query": query, "display": display}
    if sort:
        params["sort"] = sort
    raw_items = request_items(NAVER_NEWS_API_URL, params)

    articles: list[ArticleOriginal] = []
    for item in raw_items:
        published_at = _parse_pub_date(str(item.get("pubDate", "")))
        if published_at is None:
            continue
        title = strip_markup(str(item.get("title", "")))
        description = strip_markup(str(item.get("description", "")))
        original_url = str(item.get("originallink") or item.get("link") or "").strip()
        if not original_url:
            continue
        source = format_source_from_url(original_url)
        articles.append(
            ArticleOriginal(
                artist=artist,
                original_url=original_url,
                title_original=title,
                description=description,
                published_at=published_at,
                api="naver_news",
                category="news",
                source=source,
            )
        )
    return articles
