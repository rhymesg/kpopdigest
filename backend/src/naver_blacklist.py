"""Per-handler domain blacklist helpers."""

from __future__ import annotations

_BLOG_BLACKLIST = {
    "sidsisisi",
}


def is_blog_blacklisted(url: str) -> bool:
    for token in _BLOG_BLACKLIST:
        if token in url:
            return True
    return False

