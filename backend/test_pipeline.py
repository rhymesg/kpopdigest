"""CLI for running the fetch→rewrite pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from src.pipeline import PipelineError, fetch_and_rewrite


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch articles and rewrite them via ChatGPT.")
    parser.add_argument("api", choices=["naver", "daum"], help="Source API to query.")
    parser.add_argument("artist", help="Artist name (will be attached to results).")
    parser.add_argument("query", help="Search query passed to the API.")
    parser.add_argument("limit", type=int, help="Maximum number of articles to fetch and rewrite.")
    parser.add_argument(
        "--model",
        default="gpt-5-mini",
        help="OpenAI model identifier (default: gpt-5-mini).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        print("Limit must be greater than zero.", file=sys.stderr)
        return 2

    try:
        articles, results = fetch_and_rewrite(
            args.api,
            args.query,
            artist=args.artist,
            limit=args.limit,
            model=args.model,
        )
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    payload = []
    for article, result in zip(articles, results, strict=False):
        payload.append(
            {
                "artist": article.artist,
                "api": article.api,
                "category": article.category,
                "source": article.source,
                "publishedAt": article.published_at.isoformat(),
                "originalUrl": article.original_url,
                "titleOriginal": article.title_original,
                "description": article.description,
                "rewrite": result,
            }
        )

    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
