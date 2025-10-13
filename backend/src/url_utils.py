"""Utilities for resolving and validating article URLs."""

from __future__ import annotations

from typing import Tuple

import httpx

_REDIRECT_LIMIT = 5
_TIMEOUT_SECONDS = 5.0

# URL patterns that should be disabled
_BLOCKED_URL_PATTERNS = [
    "koreatimes.com/photonews",
    "yes24.com/product", 
    "seoul.co.kr/newsList/international",
    "hollywoodreporter.com/t/k-pop/",
    "imdb.com",
    "sisopick.com",
    "burgundycow.com",
    "musicscore.co.kr",
    "music.apple.com",
]


class URLResolutionError(RuntimeError):
    """Raised when a URL cannot be resolved due to configuration issues."""


def _is_failure_status(status_code: int) -> bool:
    return status_code >= 400


def is_url_blocked(url: str) -> bool:
    """Check if the URL contains any blocked patterns."""
    if not url:
        return False
    
    for pattern in _BLOCKED_URL_PATTERNS:
        if pattern in url:
            return True
    return False


def resolve_final_url(original_url: str) -> Tuple[str | None, bool]:
    """Resolve redirects for ``original_url`` and return (final_url, is_alive).

    ``final_url`` is ``None`` if resolution failed or did not change.
    ``is_alive`` is ``False`` when the URL could not be reached or returned an
    error status code.
    """

    if not original_url:
        return None, False

    try:
        with httpx.Client(
            follow_redirects=True,
            timeout=_TIMEOUT_SECONDS,
            max_redirects=_REDIRECT_LIMIT,
            headers={"User-Agent": "kpopdigest-bot/1.0"},
        ) as client:
            try:
                response = client.head(original_url)
            except httpx.RequestError:
                response = None

            if response is None or _is_failure_status(response.status_code):
                try:
                    response = client.get(original_url, headers={"Range": "bytes=0-1023"})
                except httpx.RequestError:
                    return None, False

            if response is None:
                return None, False

            if _is_failure_status(response.status_code):
                final_url = str(response.url) if response.url else None
                return final_url if final_url and final_url != original_url else None, False

            final_url = str(response.url) if response.url else None
            if not final_url or final_url == original_url:
                final_url = None
            return final_url, True
    except (httpx.RequestError, httpx.TooManyRedirects):
        return None, False
