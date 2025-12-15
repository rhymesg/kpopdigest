"""CLI for running the fetch→rewrite pipeline."""

from __future__ import annotations

import argparse
import json
import sys

from src.artist_registry import list_registered_artists
from src.llm_costs import TokenUsage, estimate_model_cost, record_usage
from src.pipeline import (
    DEFAULT_MODEL,
    PipelineError,
    fetch_and_rewrite,
    fetch_rewrite_and_store,
    fetch_rss_and_rewrite,
    fetch_rss_rewrite_and_store,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch articles and rewrite them via ChatGPT.")
    parser.add_argument(
        "--api",
        choices=["naver_news", "naver_blog", "daum", "korea_herald_rss", "all"],
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
        default=DEFAULT_MODEL,
        help=f"OpenAI model identifier (default: {DEFAULT_MODEL}).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.limit <= 0:
        print("Limit must be greater than zero.", file=sys.stderr)
        return 2

    payload: list[dict] | None = None
    usage_by_model: dict[str, TokenUsage] = {}

    try:
        include_rss = args.api in {"korea_herald_rss", "all"}
        apis = (
            ["naver_news", "naver_blog", "daum"]
            if args.api == "all"
            else ([] if args.api == "korea_herald_rss" else [args.api])
        )
        artists = args.artist if args.artist else list_registered_artists()

        if args.store:
            if include_rss:
                _, usage = fetch_rss_rewrite_and_store(
                    limit=args.limit,
                    model=args.model,
                )
                record_usage(usage_by_model, args.model, usage)

            for artist_name in artists:
                for api_choice in apis:
                    _, usage = fetch_rewrite_and_store(
                        api_choice,
                        artist=artist_name,
                        limit=args.limit,
                        model=args.model,
                    )
                    record_usage(usage_by_model, args.model, usage)
        else:
            payload = []

            if include_rss:
                rss_articles, rss_results, usage = fetch_rss_and_rewrite(
                    limit=args.limit,
                    model=args.model,
                )
                record_usage(usage_by_model, args.model, usage)
                for article, result in zip(rss_articles, rss_results, strict=False):
                    payload.append(
                        {
                            "api": article.api,
                            "category": article.category,
                            "source": article.source,
                            "sourceLanguage": article.source_language,
                            "publishedAt": article.published_at.isoformat(),
                            "originalUrl": article.original_url,
                            "titleOriginal": article.title_original,
                            "description": article.description,
                            "rewrite": result,
                        }
                    )

            for artist_name in artists:
                for api_choice in apis:
                    articles, results, usage = fetch_and_rewrite(
                        api_choice,
                        artist=artist_name,
                        limit=args.limit,
                        model=args.model,
                    )
                    record_usage(usage_by_model, args.model, usage)

                    for article, result in zip(articles, results, strict=False):
                        payload.append(
                            {
                                "artist": artist_name,
                                "api": article.api,
                                "category": article.category,
                                "source": article.source,
                                "sourceLanguage": article.source_language,
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

    if usage_by_model:
        total_cost = 0.0
        for model_name, usage in usage_by_model.items():
            cost = estimate_model_cost(model_name, usage)
            total_cost += cost
            print(
                "[pipeline] Usage",
                f"model={model_name}",
                f"input={usage.input_tokens}",
                f"cached={usage.cached_input_tokens}",
                f"output={usage.output_tokens}",
                f"estimated_cost=${cost:.4f}",
            )
        print(f"[pipeline] Estimated total cost: ${total_cost:.4f}")
    else:
        print("[pipeline] No LLM usage recorded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
