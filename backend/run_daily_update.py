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
    "naver_blog": 10,
    "daum": 20,
}

RSS_LIMIT = 20


def run_daily_update(model: str = DEFAULT_MODEL) -> None:
    artists = list_registered_artists()

    for api, limit in PER_ARTIST_CONFIG.items():
        for artist_name in artists:
            print(f"[daily] Running {api} for {artist_name} (limit={limit})")
            fetch_rewrite_and_store(
                api,  # type: ignore[arg-type]
                artist=artist_name,
                limit=limit,
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

