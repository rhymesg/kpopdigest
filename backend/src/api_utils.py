"""Utilities for normalizing publisher/source names from URLs."""

from __future__ import annotations

from urllib.parse import urlparse

_SINGLE_SUFFIXES = {
    "com",
    "net",
    "org",
    "kr",
    "jp",
    "cn",
    "us",
    "tv",
}

_DOUBLE_SUFFIXES = {
    ("co", "kr"),
    ("go", "kr"),
    ("or", "kr"),
    ("ne", "kr"),
    ("re", "kr"),
    ("pe", "kr"),
    ("ac", "kr"),
    ("co", "jp"),
    ("co", "uk"),
    ("co", "id"),
}

_HOST_PREFIX_BLACKLIST = {"www", "m", "news"}


def format_source_from_url(url: str, fallback: str = "Unknown") -> str:
    if not url:
        return fallback
    parsed = urlparse(url)
    host = parsed.hostname or parsed.netloc
    if not host:
        return fallback
    host = host.lower()

    tokens = [token for token in host.split(".") if token and token not in _HOST_PREFIX_BLACKLIST]
    if not tokens:
        tokens = [token for token in host.split(".") if token]
    if not tokens:
        return fallback

    if len(tokens) >= 3 and (tokens[-2], tokens[-1]) in _DOUBLE_SUFFIXES:
        label = tokens[-3]
    elif len(tokens) >= 2 and tokens[-1] in _SINGLE_SUFFIXES:
        label = tokens[-2]
    else:
        label = tokens[-1]

    label = label.replace("-", " ")
    if len(label) <= 4:
        return label.upper()
    return label.title()
