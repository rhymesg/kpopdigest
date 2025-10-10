"""Fetch and print BLACKPINK content from Naver and Daum search APIs."""

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

import certifi
from dotenv import load_dotenv

# Load environment variables from backend/.env if present.
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

# Naver configuration
NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
NAVER_BLOG_API_URL = "https://openapi.naver.com/v1/search/blog.json"
NAVER_CLIENT_ID_ENV = "NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET_ENV = "NAVER_CLIENT_SECRET"

# Daum configuration
DAUM_WEB_API_URL = "https://dapi.kakao.com/v2/search/web"
DAUM_API_KEY_ENV = "DAUM_REST_API_KEY"

SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

def load_naver_credentials() -> tuple[str, str]:
    client_id = os.getenv(NAVER_CLIENT_ID_ENV)
    client_secret = os.getenv(NAVER_CLIENT_SECRET_ENV)
    if not client_id or not client_secret:
        missing = [name for name, value in ((NAVER_CLIENT_ID_ENV, client_id), (NAVER_CLIENT_SECRET_ENV, client_secret)) if not value]
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return client_id, client_secret

def load_daum_credentials() -> str:
    api_key = os.getenv(DAUM_API_KEY_ENV)
    if not api_key:
        raise RuntimeError(f"Missing environment variable: {DAUM_API_KEY_ENV}")
    return api_key

def request_naver_items(api_url: str, query: str, display: int = 30, sort: str | None = None) -> list[dict]:
    params: dict[str, str] = {
        "query": query,
        "display": str(display),
    }
    if sort:
        params["sort"] = sort
    encoded_params = urllib.parse.urlencode(params)
    url = f"{api_url}?{encoded_params}"
    req = urllib.request.Request(url)

    client_id, client_secret = load_naver_credentials()
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    with urllib.request.urlopen(req, context=SSL_CONTEXT) as response:
        if response.status != 200:
            raise RuntimeError(f"Naver API request failed with status {response.status}")
        body = response.read().decode("utf-8")

    data = json.loads(body)
    return data.get("items", [])

def request_daum_items(query: str, size: int = 10, sort: str = "recency") -> list[dict]:
    params = {
        "query": query,
        "size": str(size),
        "sort": sort,
    }
    encoded_params = urllib.parse.urlencode(params)
    url = f"{DAUM_WEB_API_URL}?{encoded_params}"
    req = urllib.request.Request(url)

    api_key = load_daum_credentials()
    req.add_header("Authorization", f"KakaoAK {api_key}")

    with urllib.request.urlopen(req, context=SSL_CONTEXT) as response:
        if response.status != 200:
            raise RuntimeError(f"Daum API request failed with status {response.status}")
        body = response.read().decode("utf-8")

    data = json.loads(body)
    return data.get("documents", [])

def parse_pub_date(pub_date_raw: str) -> datetime | None:
    try:
        parsed = parsedate_to_datetime(pub_date_raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed

def parse_post_date(post_date_raw: str) -> datetime | None:
    try:
        parsed = datetime.strptime(post_date_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed

def strip_html(text: str) -> str:
    cleaned = text.replace("<b>", "").replace("</b>", "")
    return unescape(cleaned)

def print_news_items(items: list[dict], min_pub_date: datetime) -> None:
    print(f"News items since {min_pub_date.isoformat()} (total fetched: {len(items)})\n")
    matches = 0
    for item in items:
        pub_date = parse_pub_date(item.get("pubDate", ""))
        if pub_date is None or pub_date < min_pub_date:
            continue
        matches += 1
        title = strip_html(item.get("title", ""))
        description = strip_html(item.get("description", ""))
        link = item.get("link", "")
        print(f"Title      : {title}")
        print(f"Published  : {pub_date.isoformat()}")
        print(f"Summary    : {description}")
        print(f"Link       : {link}\n")

    if matches == 0:
        print("No news items found in the requested time window.\n")

def print_blog_items(items: list[dict], min_post_date: datetime) -> None:
    print(f"Blog posts since {min_post_date.date().isoformat()} (total fetched: {len(items)})\n")
    matches = 0
    for item in items:
        post_date = parse_post_date(item.get("postdate", ""))
        if post_date is None or post_date < min_post_date:
            continue
        matches += 1
        title = strip_html(item.get("title", ""))
        description = strip_html(item.get("description", ""))
        blogger_name = strip_html(item.get("bloggername", ""))
        blog_link = item.get("bloggerlink", "")
        post_link = item.get("link", "") or blog_link
        print(f"Title      : {title}")
        print(f"Published  : {post_date.date().isoformat()}")
        if blogger_name:
            print(f"Author     : {blogger_name}")
        print(f"Summary    : {description}")
        print(f"Link       : {post_link}\n")

    if matches == 0:
        print("No blog posts found in the requested time window.\n")

def print_daum_items(items: list[dict]) -> None:
    print(f"Daum web documents (total fetched: {len(items)})\n")
    if not items:
        print("No Daum web documents found.\n")
        return
    for item in items:
        title = strip_html(item.get("title", ""))
        contents = strip_html(item.get("contents", ""))
        url = item.get("url", "")
        datetime_str = item.get("datetime", "")
        print(f"Title      : {title}")
        if datetime_str:
            print(f"Timestamp  : {datetime_str}")
        print(f"Snippet    : {contents}")
        print(f"Link       : {url}\n")

def main() -> int:
    try:
        news_items = request_naver_items(NAVER_NEWS_API_URL, "블랙핑크", sort="date")
        blog_items = request_naver_items(NAVER_BLOG_API_URL, "블랙핑크", sort="date")
        daum_items = request_daum_items("블랙핑크")
    except Exception as exc:
        print(f"Error fetching content: {exc}", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    print_news_items(news_items, cutoff)
    print_blog_items(blog_items, cutoff)
    print_daum_items(daum_items)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
