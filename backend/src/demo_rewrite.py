"""CLI helper to test article rewrites via the OpenAI API."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

from .article_models import ArticleOriginal
from .chatgpt_client import ChatGPTClient, ChatGPTRewriteError


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Send a rewrite request to ChatGPT.")
    parser.add_argument("--artist", required=True, help="Artist name to evaluate relevance.")
    parser.add_argument(
        "--category",
        default="news",
        help="Content category (e.g. news, blog, community).",
    )
    parser.add_argument(
        "--source",
        default="Unknown Source",
        help="Source outlet or site name.",
    )
    parser.add_argument(
        "--url",
        default="https://example.com",
        help="Original article URL (default: https://example.com).",
    )
    parser.add_argument(
        "--published",
        default=None,
        help="Published timestamp in ISO-8601 (default: now, UTC).",
    )
    parser.add_argument(
        "--api",
        default="demo",
        help="Source API identifier (default: demo).",
    )
    parser.add_argument("--title", required=True, help="Original title in Korean.")
    parser.add_argument(
        "--description",
        required=True,
        help="Original description or snippet in Korean.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-mini",
        help="OpenAI model identifier (default: gpt-5-mini).",
    )
    return parser.parse_args()


def _resolve_published(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "--published must be ISO-8601 formatted (e.g. 2024-05-20T08:00:00+09:00)."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def main() -> int:
    args = parse_args()
    try:
        published_at = _resolve_published(args.published)
    except argparse.ArgumentTypeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    article = ArticleOriginal(
        artist=args.artist,
        original_url=args.url,
        title_original=args.title,
        description=args.description,
        published_at=published_at,
        api=args.api,
        category=args.category,
        source=args.source,
        source_language="ko",
    )

    try:
        client = ChatGPTClient(model=args.model)
        result = client.rewrite(article)
    except ChatGPTRewriteError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
