"""Daum Search API helpers returning normalized article records."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from html import unescape
from typing import Any, Mapping

import certifi

from .article_models import ArticleOriginal
from .api_utils import format_source_from_url

DAUM_WEB_API_URL = "https://dapi.kakao.com/v2/search/web"
DAUM_API_KEY_ENV = "DAUM_REST_API_KEY"

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class DaumApiError(RuntimeError):
    """Raised when a Daum API request fails."""


def _strip_markup(value: str) -> str:
    return unescape(value.replace("<b>", "").replace("</b>", ""))


def _load_api_key() -> str:
    api_key = os.getenv(DAUM_API_KEY_ENV)
    if not api_key:
        raise DaumApiError(f"Missing environment variable: {DAUM_API_KEY_ENV}")
    return api_key


def _request_items(params: Mapping[str, Any]) -> list[dict[str, Any]]:
    encoded = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
    req = urllib.request.Request(f"{DAUM_WEB_API_URL}?{encoded}")
    req.add_header("Authorization", f"KakaoAK {_load_api_key()}")

    try:
        with urllib.request.urlopen(req, context=_SSL_CONTEXT) as response:
            if response.status != 200:
                raise DaumApiError(f"HTTP {response.status} from Daum API")
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - network
        raise DaumApiError(f"Failed to call Daum API: {exc}") from exc

    data = json.loads(body)
    return list(data.get("documents", []))


from urllib.parse import urlparse


_BLOG_HOST_TOKENS = {
    "blog",
    "tistory",
    "medium",
}

_COMMUNITY_HOST_TOKENS = {
    "dcinside",
    "theqoo",
    "instiz",
    "fmkorea",
    "gall",
    "ppomppu",
    "pann",
}

_VIDEO_HOST_TOKENS = {
    "youtube",
    "youtu.be",
}


def _infer_category(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if any(token in host for token in _BLOG_HOST_TOKENS):
        return "blog"
    if any(token in host for token in _COMMUNITY_HOST_TOKENS):
        return "community"
    if any(token in host for token in _VIDEO_HOST_TOKENS):
        return "etc"
    return "news"


def fetch_daum_web(
    query: str,
    *,
    artist: str,
    size: int = 10,
    sort: str = "recency",
) -> list[ArticleOriginal]:
    """Fetch Daum web search results and normalize them."""

    params: dict[str, Any] = {"query": query, "size": size, "sort": sort}
    raw_items = _request_items(params)

    articles: list[ArticleOriginal] = []
    for item in raw_items:
        url = str(item.get("url") or "").strip()
        if not url:
            continue
        datetime_raw = str(item.get("datetime") or "").strip()
        try:
            published_at = datetime.fromisoformat(datetime_raw.replace("Z", "+00:00"))
        except ValueError:
            continue
        title = _strip_markup(str(item.get("title", "")))
        description = _strip_markup(str(item.get("contents", "")))
        category = _infer_category(url)
        source = format_source_from_url(url)
        articles.append(
            ArticleOriginal(
                artist=artist,
                original_url=url,
                title_original=title,
                description=description,
                published_at=published_at,
                api="daum",
                category=category,
                source=source,
            )
        )
    return articles
