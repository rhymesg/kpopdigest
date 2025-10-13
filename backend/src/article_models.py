"""Shared data structures for fetched articles."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class ArticleOriginal:
    """Raw article metadata as returned by an upstream provider."""

    artist: str | None
    original_url: str
    title_original: str
    description: str
    published_at: datetime
    api: str
    category: str
    source: str
