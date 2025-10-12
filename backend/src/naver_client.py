"""Shared request helpers for the Naver OpenAPI."""

from __future__ import annotations

import json
import os
import ssl
import urllib.error
import urllib.parse
import urllib.request
from html import unescape
from typing import Any, Mapping

import certifi

NAVER_CLIENT_ID_ENV = "NAVER_CLIENT_ID"
NAVER_CLIENT_SECRET_ENV = "NAVER_CLIENT_SECRET"

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def strip_markup(value: str) -> str:
    return unescape(value.replace("<b>", "").replace("</b>", ""))


def request_items(api_url: str, params: Mapping[str, Any]) -> list[dict[str, Any]]:
    encoded = urllib.parse.urlencode({k: str(v) for k, v in params.items()})
    req = urllib.request.Request(f"{api_url}?{encoded}")

    client_id = os.getenv(NAVER_CLIENT_ID_ENV)
    client_secret = os.getenv(NAVER_CLIENT_SECRET_ENV)
    if not client_id or not client_secret:
        missing = [
            name
            for name, val in (
                (NAVER_CLIENT_ID_ENV, client_id),
                (NAVER_CLIENT_SECRET_ENV, client_secret),
            )
            if not val
        ]
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")

    req.add_header("X-Naver-Client-Id", client_id)
    req.add_header("X-Naver-Client-Secret", client_secret)

    try:
        with urllib.request.urlopen(req, context=_SSL_CONTEXT) as response:
            if response.status != 200:
                raise RuntimeError(f"HTTP {response.status} from Naver API")
            body = response.read().decode("utf-8")
    except urllib.error.URLError as exc:  # pragma: no cover - network
        raise RuntimeError(f"Failed to call Naver API: {exc}") from exc

    data = json.loads(body)
    return list(data.get("items", []))


__all__ = ["strip_markup", "request_items"]
