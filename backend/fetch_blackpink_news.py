"""Fetch and print BLACKPINK content from Naver and Daum search APIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from src.article_models import ArticleOriginal
from src.daum_api import fetch_daum_web
from src.naver_api import fetch_naver_blog_posts, fetch_naver_news

ARTIST = "BLACKPINK"
QUERY = "블랙핑크"


def _print_articles(label: str, articles: Iterable[ArticleOriginal], cutoff: datetime | None = None) -> None:
    print(f"{label}\n")
    matches = 0
    for article in articles:
        if cutoff and article.published_at < cutoff:
            continue
        matches += 1
        print(f"Title       : {article.title_original}")
        print(f"Source      : {article.source}")
        print(f"Category    : {article.category}")
        print(f"Published   : {article.published_at.isoformat()}")
        print(f"API         : {article.api}")
        print(f"Original URL: {article.original_url}")
        print(f"Description : {article.description}\n")

    if matches == 0:
        print("No matching articles in the requested time window.\n")


def main() -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=3)

    naver_news = fetch_naver_news(QUERY, artist=ARTIST)
    naver_blog = fetch_naver_blog_posts(QUERY, artist=ARTIST)
    daum_web = fetch_daum_web(QUERY, artist=ARTIST)

    _print_articles("Naver news items", naver_news, cutoff)
    _print_articles("Naver blog posts", naver_blog, cutoff)
    _print_articles("Daum web documents", daum_web, cutoff)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
