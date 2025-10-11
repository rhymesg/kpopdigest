"""Naver Search API helpers returning normalized article records."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any, Mapping
from urllib.parse import urlparse

import certifi

from .article_models import ArticleOriginal

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
NAVER_BLOG_API_URL = "https://openapi.naver.com/v1/search/blog.json"
NAVER_CLIENT_ID_ENV = "NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET_ENV = "NAVER_CLIENT_SECRET"

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class NaverApiError(RuntimeError):
    """Raised when a Naver API request fails."""


def _strip_markup(value: str) -> str:
    return unescape(value.replace("<b>", "").replace("</b>", ""))


def _load_credentials() -> tuple[str, str]:
    client_id = os.getenv(NAVER_CLIENT_ID_ENV)
    client_secret = os.getenv(NAVER_CLIENT_SECRET_ENV)
    if not client_id or not client_secret:
        missing = [
            name
            for name, val in (
                (NAVER_CLIENT_ID_ENV, client_id),
                (NAVER_CLIENT_SECRET_ENV, client_secret),
            )
            if not val
        ]
        raise NaverApiError(f"Missing environment variables: {', '.join(missing)}")
    return client_id, client_secret


def _request_items(api_url: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    encoded = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
    req = urllib.request.Request(f"{api_url}?{encoded}")

    client_id, client_secret = _load_credentials()
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    try:
        with urllib.request.urlopen(req, context=_SSL_CONTEXT) as response:
            if response.status != 200:
                raise NaverApiError(f"HTTP {response.status} from Naver API")
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - network
        raise NaverApiError(f"Failed to call Naver API: {exc}") from exc

    data = json.loads(body)
    return list(data.get("items", []))


def _parse_pub_date(pub_date_raw: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(pub_date_raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _parse_post_date(post_date_raw: str) -> datetime | None:
    try:
        parsed = datetime.strptime(post_date_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed


_SINGLE_SUFFIXES = {
    "com",
    "net",
    "org",
    "kr",
    "jp",
    "cn",
    "us",
    "tv",
}

_DOUBLE_SUFFIXES = {
    ("co", "kr"),
    ("go", "kr"),
    ("or", "kr"),
    ("ne", "kr"),
    ("re", "kr"),
    ("pe", "kr"),
    ("ac", "kr"),
    ("co", "jp"),
    ("co", "uk"),
    ("co", "id"),
}

_HOST_PREFIX_BLACKLIST = {"www", "m", "news"}
_COMMUNITY_DOMAINS = {"pann.nate.com"}


def _format_source_from_url(url: str, fallback: str = "Unknown") -> str:
    if not url:
        return fallback
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc
    if not host:
        return fallback
    host = host.lower()

    tokens = [token for token in host.split(".") if token and token not in _HOST_PREFIX_BLACKLIST]
    if not tokens:
        tokens = [token for token in host.split(".") if token]
    if not tokens:
        return fallback

    label: str
    if len(tokens) >= 3 and (tokens[-2], tokens[-1]) in _DOUBLE_SUFFIXES:
        label = tokens[-3]
    elif len(tokens) >= 2 and tokens[-1] in _SINGLE_SUFFIXES:
        label = tokens[-2]
    else:
        label = tokens[-1]

    label = label.replace("-", " ")
    if len(label) <= 4:
        return label.upper()
    return label.title()


def _infer_category(url: str) -> str:
    host = urlparse(url).hostname or ""
    host = host.lower()
    if host in _COMMUNITY_DOMAINS or any(host.endswith(f".{domain}") for domain in _COMMUNITY_DOMAINS):
        return "community"
    return "news"


def fetch_naver_news(
    query: str,
    *,
    artist: str,
    display: int = 30,
    sort: str | None = "date",
) -> list[ArticleOriginal]:
    """Fetch Naver news search results and normalize them."""

    params: dict[str, Any] = {"query": query, "display": display}
    if sort:
        params["sort"] = sort
    raw_items = _request_items(NAVER_NEWS_API_URL, params)

    articles: list[ArticleOriginal] = []
    for item in raw_items:
        published_at = _parse_pub_date(str(item.get("pubDate", "")))
        if published_at is None:
            continue
        title = _strip_markup(str(item.get("title", "")))
        description = _strip_markup(str(item.get("description", "")))
        original_url = str(item.get("originallink") or item.get("link") or "").strip()
        if not original_url:
            continue
        source = _format_source_from_url(original_url)
        category = _infer_category(original_url)
        articles.append(
            ArticleOriginal(
                artist=artist,
                original_url=original_url,
                title_original=title,
                description=description,
                published_at=published_at,
                api="naver",
                category=category,
                source=source,
            )
        )
    return articles


def fetch_naver_blog_posts(
    query: str,
    *,
    artist: str,
    display: int = 30,
    sort: str | None = "date",
) -> list[ArticleOriginal]:
    """Fetch Naver blog search results and normalize them."""

    params: dict[str, Any] = {"query": query, "display": display}
    if sort:
        params["sort"] = sort
    raw_items = _request_items(NAVER_BLOG_API_URL, params)

    articles: list[ArticleOriginal] = []
    for item in raw_items:
        published_at = _parse_post_date(str(item.get("postdate", "")))
        if published_at is None:
            continue
        title = _strip_markup(str(item.get("title", "")))
        description = _strip_markup(str(item.get("description", "")))
        original_url = str(item.get("link") or item.get("bloggerlink") or "").strip()
        if not original_url:
            continue
        source_raw = str(item.get("bloggername") or "").strip()
        source = source_raw or _format_source_from_url(original_url)
        articles.append(
            ArticleOriginal(
                artist=artist,
                original_url=original_url,
                title_original=title,
                description=description,
                published_at=published_at,
                api="naver",
                category="blog",
                source=source,
            )
        )
    return articles
