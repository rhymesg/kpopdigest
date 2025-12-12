"""Daily pipeline runner without CLI arguments."""

from __future__ import annotations

from typing import Iterable

from src.artist_registry import list_registered_artists
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


def run_daily_update(model: str = DEFAULT_MODEL) -> None:
    artists = list_registered_artists()

    for api, limit in PER_ARTIST_CONFIG.items():
        for artist_name in artists:
            limit_for_artist = _get_artist_limit(artist_name, limit)
            if limit_for_artist <= 0:
                print(
                    f"[daily] Skipping {api} for {artist_name} (ratio=0, limit={limit_for_artist})"
                )
                continue
            print(
                f"[daily] Running {api} for {artist_name} (limit={limit_for_artist})"
            )
            fetch_rewrite_and_store(
                api,  # type: ignore[arg-type]
                artist=artist_name,
                limit=limit_for_artist,
                model=model,
            )

    print("[daily] Running korea_herald_rss (limit=20)")
    fetch_rss_rewrite_and_store(limit=RSS_LIMIT, model=model)


def main() -> int:
    try:
        run_daily_update()
    except PipelineError as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


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
