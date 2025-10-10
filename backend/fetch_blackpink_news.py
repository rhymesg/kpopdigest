"""Fetch recent BLACKPINK news/blog entries from Naver Open API and print filtered results."""

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

NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
BLOG_API_URL = "https://openapi.naver.com/v1/search/blog.json"
CLIENT_ID_ENV = "NAVER_CLIENT_ID"
CLIENT_SECRET_ENV = "NAVER_CLIENT_SECRET"
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())

def load_credentials() -> tuple[str, str]:
    """Load API credentials from environment variables."""
    client_id = os.getenv(CLIENT_ID_ENV)
    client_secret = os.getenv(CLIENT_SECRET_ENV)
    if not client_id or not client_secret:
        missing = [name for name, value in ((CLIENT_ID_ENV, client_id), (CLIENT_SECRET_ENV, client_secret)) if not value]
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return client_id, client_secret

def request_items(api_url: str, query: str, display: int = 30, sort: str | None = None) -> list[dict]:
    """Call a Naver Search API endpoint and return the raw items list."""
    params: dict[str, str] = {
        "query": query,
        "display": str(display),
    }
    if sort:
        params["sort"] = sort
    encoded_params = urllib.parse.urlencode(params)
    url = f"{api_url}?{encoded_params}"
    req = urllib.request.Request(url)

    client_id, client_secret = load_credentials()
    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    with urllib.request.urlopen(req, context=SSL_CONTEXT) as response:
        if response.status != 200:
            raise RuntimeError(f"Naver API request failed with status {response.status}")
        body = response.read().decode("utf-8")

    data = json.loads(body)
    return data.get("items", [])

def parse_pub_date(pub_date_raw: str) -> datetime | None:
    """Convert Naver's news pubDate string to a timezone-aware datetime."""
    try:
        parsed = parsedate_to_datetime(pub_date_raw)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed

def parse_post_date(post_date_raw: str) -> datetime | None:
    """Convert Naver's blog postdate (YYYYMMDD) to a timezone-aware datetime."""
    try:
        parsed = datetime.strptime(post_date_raw, "%Y%m%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed

def strip_html(text: str) -> str:
    """Remove simple HTML tags and decode HTML entities."""
    cleaned = text.replace("<b>", "").replace("</b>", "")
    return unescape(cleaned)

def print_news_items(items: list[dict], min_pub_date: datetime) -> None:
    """Print news items published on or after the given datetime."""
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
    """Print blog items published on or after the given datetime."""
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

def main() -> int:
    try:
        news_items = request_items(NEWS_API_URL, "블랙핑크", sort="date")
        blog_items = request_items(BLOG_API_URL, "블랙핑크", sort="date")
    except Exception as exc:
        print(f"Error fetching content: {exc}", file=sys.stderr)
        return 1

    cutoff = datetime.now(timezone.utc) - timedelta(days=3)
    print_news_items(news_items, cutoff)
    print_blog_items(blog_items, cutoff)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
