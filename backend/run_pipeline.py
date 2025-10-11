"""CLI for running the fetch→rewrite pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from src.artist_registry import list_registered_artists
from src.pipeline import (
    PipelineError,
    fetch_and_rewrite,
    fetch_rewrite_and_store,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch articles and rewrite them via ChatGPT.")
    parser.add_argument(
        "--api",
        choices=["naver", "daum", "all"],
        default="all",
        help="Source API to query (default: all).",
    )
    parser.add_argument(
        "--artist",
        action="append",
        help="Artist name (canonical label). Provide multiple times or omit to process all registered artists.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Maximum number of articles to fetch per artist (default: 50).",
    )
    parser.add_argument(
        "--store",
        action="store_true",
        help="Persist new articles to the database using fetch_rewrite_and_store.",
    )
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

    payload: list[dict] | None = None

    try:
        apis = [args.api] if args.api != "all" else ["naver", "daum"]
        artists = args.artist if args.artist else list_registered_artists()

        if args.store:
            for artist_name in artists:
                for api_choice in apis:
                    fetch_rewrite_and_store(
                        api_choice,
                        artist=artist_name,
                        limit=args.limit,
                        model=args.model,
                    )
        else:
            payload = []
            for artist_name in artists:
                for api_choice in apis:
                    articles, results = fetch_and_rewrite(
                        api_choice,
                        artist=artist_name,
                        limit=args.limit,
                        model=args.model,
                    )

                    for article, result in zip(articles, results, strict=False):
                        payload.append(
                            {
                                "artist": artist_name,
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
    except PipelineError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if not args.store and payload is not None:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
