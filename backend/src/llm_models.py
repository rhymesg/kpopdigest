"""Common data structures for building ChatGPT rewrite payloads."""

from __future__ import annotations

from html import unescape
import re
from typing import TypedDict

from .article_models import ArticleOriginal

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_markup(text: str) -> str:
    """Remove basic HTML tags and decode entities."""
    if not isinstance(text, str):
        text = "" if text is None else str(text)
    without_tags = _TAG_RE.sub("", text)
    return unescape(without_tags)


class ChatGPTRewriteInput(TypedDict):
    artist: str
    category: str
    source: str
    titleOriginal: str
    description: str


class ChatGPTRewriteOutput(TypedDict):
    relevant: bool
    titleRaw: str
    title: str
    summary: str


def build_rewrite_input(article: ArticleOriginal) -> ChatGPTRewriteInput:
    """Convert an ArticleOriginal into the payload shape expected by ChatGPT."""

    return {
        "artist": article.artist,
        "category": article.category,
        "source": article.source,
        "titleOriginal": _strip_markup(article.title_original),
        "description": _strip_markup(article.description),
    }
