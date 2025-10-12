"""Utilities for calling the OpenAI Responses API."""

from __future__ import annotations

import json
import os
from typing import Any, cast

from openai import OpenAI, OpenAIError

from .article_models import ArticleOriginal
from .llm_models import ChatGPTRewriteOutput, build_rewrite_input


class ChatGPTRewriteError(RuntimeError):
    """Raised when the rewrite request fails or the response is invalid."""


class ChatGPTClient:
    """Thin wrapper around the OpenAI Responses API for article rewrites."""

    _SYSTEM_PROMPT = (
        "You are an assistant that analyzes and rewrites K-pop related web pages "
        "for an English-speaking fan audience. Follow these rules strictly:\n"
        "1. Determine if the page is mainly about the provided artist using the "
        "titleOriginal, description, category, and source metadata.\n"
        "2. Respond ONLY with JSON containing the keys relevant, titleRaw, title, "
        "and summary.\n"
        "3. If the page is not relevant, set relevant to false and leave the other "
        "fields as empty strings. Do not add any extra text.\n"
        "4. If the page is relevant, set relevant to true and:\n"
        "   - titleRaw: translate titleOriginal literally into clear English.\n"
        "   - title: write a catchy, natural English headline for fans of the "
        "artist, using light K-pop slang if it fits.\n"
        "   - summary: write a single concise sentence (under 30 words) highlighting "
        "the key takeaway and, if obvious, note whether it reads like news, a blog "
        "post, or a community/photo update.\n"
        "5. If the page is a community update with no clear photo or video content, treat it as not relevant."
    )

    def __init__(self, *, api_key: str | None = None, model: str = "gpt-5-mini") -> None:
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ChatGPTRewriteError("OPENAI_API_KEY is not set. Add it to backend/.env.")
        self._client = OpenAI(api_key=key)
        self._model = model

    def rewrite(self, article: ArticleOriginal) -> ChatGPTRewriteOutput:
        """Call the OpenAI Responses API and return normalized rewrite output."""

        request_payload = build_rewrite_input(article)
        user_content = (
            "### Input\n"
            f"{json.dumps(request_payload, ensure_ascii=False, sort_keys=True)}\n"
            "Follow the formatting instructions exactly."
        )
        try:
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": self._SYSTEM_PROMPT},
                    {"role": "user", "content": user_content},
                ],
            )
        except OpenAIError as exc:  # pragma: no cover - requires network
            raise ChatGPTRewriteError(f"OpenAI request failed: {exc}") from exc

        raw_text = response.output_text
        try:
            parsed: dict[str, Any] = json.loads(raw_text)
        except json.JSONDecodeError as exc:  # pragma: no cover - invalid model output
            raise ChatGPTRewriteError("OpenAI response was not valid JSON.") from exc

        missing = [key for key in ("relevant", "titleRaw", "title", "summary") if key not in parsed]
        if missing:
            raise ChatGPTRewriteError(
                f"OpenAI response missing required fields: {', '.join(missing)}"
            )

        relevant_raw = parsed["relevant"]
        if isinstance(relevant_raw, str):
            relevant = relevant_raw.strip().lower() in {"true", "yes", "1"}
        else:
            relevant = bool(relevant_raw)

        return cast(
            ChatGPTRewriteOutput,
            {
                "relevant": relevant,
                "titleRaw": str(parsed["titleRaw"]),
                "title": str(parsed["title"]),
                "summary": str(parsed["summary"]),
            },
        )
