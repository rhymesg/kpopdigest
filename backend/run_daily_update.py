"""Daily pipeline runner without CLI arguments."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from src.artist_registry import list_registered_artists
from src.llm_costs import TokenUsage, estimate_model_cost, record_usage
from src.pipeline import (
    DEFAULT_MODEL,
    fetch_rewrite_and_store,
    fetch_rss_rewrite_and_store,
    PipelineError,
)

PER_ARTIST_CONFIG: dict[str, int] = {
    "naver_news": 20,
    "naver_blog": 5,
    "daum": 20,
}

ARTIST_FETCH_RATIOS: dict[str, float] = {
    "NEWJEANS": 0.5,
    "TWICE": 0.5,
    "ENHYPEN": 0.5,
    "SEVENTEEN": 0.5,
    "TRESURE": 0.5,
}

RSS_LIMIT = 20


def run_daily_update(*, model: str, usage_bucket: dict[str, TokenUsage]) -> None:
    """Run all artist fetch/store jobs and accumulate usage in the provided bucket."""

    artists = list_registered_artists()

    for api, limit in PER_ARTIST_CONFIG.items():
        for artist_name in artists:
            limit_for_artist = _get_artist_limit(artist_name, limit)
            if limit_for_artist <= 0:
                print(
                    f"[daily] Skipping {api} for {artist_name} (ratio=0, limit={limit_for_artist})"
                )
                continue
            print(f"[daily] Running {api} for {artist_name} (limit={limit_for_artist})")
            _, usage = fetch_rewrite_and_store(
                api,  # type: ignore[arg-type]
                artist=artist_name,
                limit=limit_for_artist,
                model=model,
            )
            record_usage(usage_bucket, model, usage)

    print(f"[daily] Running korea_herald_rss (limit={RSS_LIMIT})")
    _, rss_usage = fetch_rss_rewrite_and_store(limit=RSS_LIMIT, model=model)
    record_usage(usage_bucket, model, rss_usage)


def _print_cost_report(usage_bucket: dict[str, TokenUsage]) -> None:
    if not usage_bucket:
        print("[daily] No LLM usage recorded.")
        return

    total_cost = 0.0
    for model_name, usage in usage_bucket.items():
        cost = estimate_model_cost(model_name, usage)
        total_cost += cost
        print(
            "[daily] Usage",
            f"model={model_name}",
            f"input={usage.input_tokens}",
            f"cached={usage.cached_input_tokens}",
            f"output={usage.output_tokens}",
            f"estimated_cost=${cost:.4f}",
        )
    print(f"[daily] Estimated total cost: ${total_cost:.4f}")


def main() -> int:
    usage_bucket: dict[str, TokenUsage] = {}
    start = datetime.now()
    print(f"[daily] Started at {start.isoformat(sep=' ', timespec='seconds')}")
    try:
        run_daily_update(model=DEFAULT_MODEL, usage_bucket=usage_bucket)
    except PipelineError as exc:
        print(f"Error: {exc}")
        return 1
    finally:
        end = datetime.now()
        print(f"[daily] Finished at {end.isoformat(sep=' ', timespec='seconds')}")
        _print_cost_report(usage_bucket)
        print()
    return 0


def _get_artist_limit(artist_name: str, default_limit: int) -> int:
    """Return the fetch limit after applying any artist-specific ratio."""

    ratio = ARTIST_FETCH_RATIOS.get(artist_name.upper(), 1.0)
    ratio = max(0.0, min(1.0, ratio))  # clamp to [0, 1]
    if ratio == 0 or default_limit <= 0:
        return 0
    adjusted = int(round(default_limit * ratio))
    if adjusted == 0:
        adjusted = 1  # still fetch at least one item when ratio > 0
    return adjusted


if __name__ == "__main__":
    raise SystemExit(main())
