"""Utilities for calling the OpenAI Responses API."""

from __future__ import annotations

import json
import os
from typing import Any, Sequence, cast

from openai import OpenAI, OpenAIError

from .article_models import ArticleOriginal
from .llm_models import (
    ChatGPTRewriteOutput,
    ChatGPTRSSRewriteOutput,
    build_rewrite_input,
    build_rss_rewrite_input,
)


class ChatGPTRewriteError(RuntimeError):
    """Raised when the rewrite request fails or the response is invalid."""


class ChatGPTClient:
    """Thin wrapper around the OpenAI Responses API for article rewrites."""

    _COMMON_REWRITE_RULES = (
        "4. If the page is relevant, set relevant to true and:\n"
        "   - titleRaw: translate titleOriginal literally into clear English.\n"
        "   - title: write a catchy, natural English headline (85 characters or fewer) "
        "for fans of the artist, using light K-pop slang if it fits.\n"
        "   - summary: write a single concise sentence (under 30 words) that highlights "
        "the key takeaway, and if it is obviously a video clip, photo set, or text "
        "write-up, mention that content type. Skip news/blog/community labels.\n"
        "5. If the page is a community update with no clear photo or video content, treat it as not relevant.\n"
        "6. Treat pages as not relevant if they look like click-bait spam, fortune telling, unrelated product ads, or posts that only keyword-stuff the artist name without actual coverage."
    )

    _SYSTEM_PROMPT = (
        "You are an assistant that analyzes and rewrites K-pop related web pages "
        "for an English-speaking fan audience. Follow these rules strictly:\n"
        "1. Determine if the page is mainly about the provided artist using the "
        "titleOriginal, description, category, and source metadata.\n"
        "2. Respond ONLY with JSON containing the keys relevant, titleRaw, title, "
        "and summary.\n"
        "3. If the page is not relevant, set relevant to false and leave the other "
        "fields as empty strings. Do not add any extra text.\n"
        f"{_COMMON_REWRITE_RULES}"
    )

    _SYSTEM_PROMPT_RSS = (
        "You analyze K-pop RSS feed entries for an English-speaking fan audience. "
        "Follow these rules strictly:\n"
        "1. Review titleOriginal, description, category, source, and candidateArtists from the input to decide which listed artists the article clearly covers.\n"
        "2. Respond ONLY with JSON containing the keys relevant, titleRaw, title, summary, and artists.\n"
        "3. If no candidate artist is clearly covered, set relevant to false, return empty strings for the other text fields, and set artists to an empty list.\n"
        f"{_COMMON_REWRITE_RULES}\n"
        "7. Always set artists to the list (in candidateArtists order) of artists that match the article; never invent new names."
    )

    def __init__(self, *, api_key: str | None = None, model: str) -> None:
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

        missing = [key for key in ("titleRaw", "title", "summary") if key not in parsed]
        if missing:
            raise ChatGPTRewriteError(
                f"OpenAI response missing required fields: {', '.join(missing)}"
            )

        relevant_present = "relevant" in parsed
        relevant_raw = parsed.get("relevant")
        if isinstance(relevant_raw, str):
            relevant = relevant_raw.strip().lower() in {"true", "yes", "1"}
        else:
            relevant = bool(relevant_raw) if relevant_present else None

        title_raw = str(parsed.get("titleRaw") or "")
        title = str(parsed.get("title") or "")
        summary = str(parsed.get("summary") or "")

        if relevant is None:
            print(
                f"[chatgpt] Warning: 'relevant' missing in rewrite response for {article.original_url}.",
                "Inferring from content.",
                flush=True,
            )
            has_content = bool(title.strip() or summary.strip())
            relevant = has_content

        return cast(
            ChatGPTRewriteOutput,
            {
                "relevant": relevant,
                "titleRaw": title_raw,
                "title": title,
                "summary": summary,
            },
        )

    def rewrite_rss(
        self, article: ArticleOriginal, *, candidate_artists: Sequence[str]
    ) -> ChatGPTRSSRewriteOutput:
        """Rewrite an RSS article and extract relevant artists."""

        request_payload = build_rss_rewrite_input(article, candidate_artists)
        user_content = (
            "### Input\n"
            f"{json.dumps(request_payload, ensure_ascii=False, sort_keys=True)}\n"
            "Follow the formatting instructions exactly."
        )
        try:
            response = self._client.responses.create(
                model=self._model,
                input=[
                    {"role": "system", "content": self._SYSTEM_PROMPT_RSS},
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

        missing = [
            key
            for key in ("titleRaw", "title", "summary", "artists")
            if key not in parsed
        ]
        if missing:
            raise ChatGPTRewriteError(
                f"OpenAI response missing required fields: {', '.join(missing)}"
            )

        relevant_present = "relevant" in parsed
        relevant_raw = parsed.get("relevant")
        if isinstance(relevant_raw, str):
            relevant = relevant_raw.strip().lower() in {"true", "yes", "1"}
        else:
            relevant = bool(relevant_raw) if relevant_present else None

        artists_raw = parsed["artists"]
        if isinstance(artists_raw, str):
            tokens = [token.strip() for token in artists_raw.split(",")]
        elif isinstance(artists_raw, list):
            tokens = [str(token).strip() for token in artists_raw]
        else:
            raise ChatGPTRewriteError("OpenAI response field 'artists' must be a list or comma separated string.")

        candidate_lookup = {name.strip().upper(): name.strip() for name in candidate_artists if name and name.strip()}
        artists: list[str] = []
        seen: set[str] = set()
        for token in tokens:
            if not token:
                continue
            key = token.upper()
            mapped = candidate_lookup.get(key)
            if not mapped:
                continue
            if key in seen:
                continue
            seen.add(key)
            artists.append(mapped)

        if relevant_present is False:
            print(
                f"[chatgpt] Warning: 'relevant' missing in RSS rewrite response for {article.original_url}.",
                "Inferring from content.",
                flush=True,
            )

        title_raw = str(parsed.get("titleRaw") or "")
        title = str(parsed.get("title") or "")
        summary = str(parsed.get("summary") or "")

        if relevant is None:
            has_content = bool(artists or title.strip() or summary.strip())
            relevant = has_content

        if relevant and not artists:
            # Model marked the article as relevant but failed to map artists to the registry.
            raise ChatGPTRewriteError(
                "OpenAI response marked article relevant but did not return any known artists."
            )

        return cast(
            ChatGPTRSSRewriteOutput,
            {
                "relevant": relevant,
                "titleRaw": title_raw,
                "title": title,
                "summary": summary,
                "artists": artists if relevant else [],
            },
        )
