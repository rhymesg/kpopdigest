"""Naver Blog API helpers returning normalized article records."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Mapping

import certifi

from .article_models import ArticleOriginal
from .naver_client import request_items, strip_markup

NAVER_BLOG_API_URL = "https://openapi.naver.com/v1/search/blog.json"

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class NaverBlogApiError(RuntimeError):
    """Raised when a Naver blog API request fails."""


def _parse_post_date(post_date_raw: str) -> datetime | None:
    try:
        parsed = datetime.strptime(post_date_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed


def fetch_naver_blog_posts(
    query: str,
    *,
    artist: str,
    display: int = 30,
    sort: str | None = "date",
) -> list[ArticleOriginal]:
    params: dict[str, Any] = {"query": query, "display": display}
    if sort:
        params["sort"] = sort
    raw_items = request_items(NAVER_BLOG_API_URL, params)

    articles: list[ArticleOriginal] = []
    for item in raw_items:
        published_at = _parse_post_date(str(item.get("postdate", "")))
        if published_at is None:
            continue
        title = strip_markup(str(item.get("title", "")))
        description = strip_markup(str(item.get("description", "")))
        original_url = str(item.get("link") or item.get("bloggerlink") or "").strip()
        if not original_url:
            continue
        source = "Naver Blog"
        articles.append(
            ArticleOriginal(
                artist=artist,
                original_url=original_url,
                title_original=title,
                description=description,
                published_at=published_at,
                api="naver_blog",
                category="blog",
                source=source,
            )
        )
    return articles
