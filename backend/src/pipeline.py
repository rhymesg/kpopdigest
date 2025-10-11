"""End-to-end helpers to fetch articles, rewrite them, and persist results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from typing import Literal, Sequence, Tuple

import psycopg

from .article_models import ArticleOriginal
from .chatgpt_client import ChatGPTClient, ChatGPTRewriteError
from .daum_api import fetch_daum_web
from .db import DatabaseError, ensure_article_table, get_connection
from .llm_models import ChatGPTRewriteOutput
from .naver_api import fetch_naver_news
from .url_utils import resolve_final_url

SupportedAPI = Literal["naver", "daum"]


class PipelineError(RuntimeError):
    """Raised when the fetch → rewrite pipeline fails."""


@dataclass(slots=True)
class RewriteResult:
    article: ArticleOriginal
    rewrite: ChatGPTRewriteOutput


def _fetch_articles(api: SupportedAPI, query: str, *, artist: str, limit: int) -> list[ArticleOriginal]:
    if limit <= 0:
        return []

    if api == "naver":
        return fetch_naver_news(query, artist=artist, display=limit)[:limit]
    if api == "daum":
        return fetch_daum_web(query, artist=artist, size=limit)[:limit]

    raise PipelineError(f"Unsupported API: {api}")


def fetch_and_rewrite(
    api: SupportedAPI,
    query: str,
    *,
    artist: str,
    limit: int,
    model: str = "gpt-5-mini",
) -> Tuple[Sequence[ArticleOriginal], Sequence[ChatGPTRewriteOutput]]:
    """Fetch articles from the chosen API and rewrite them via ChatGPT."""

    print(f"[pipeline] Fetching up to {limit} '{api}' results for artist '{artist}' and query '{query}'...")
    articles = _fetch_articles(api, query, artist=artist, limit=limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return articles, []

    client = ChatGPTClient(model=model)
    print(f"[pipeline] Running rewrites with model '{model}'...")
    rewrites: list[ChatGPTRewriteOutput] = []
    total = min(len(articles), limit)
    for index, article in enumerate(articles[:limit], start=1):
        print(
            f"[pipeline] ({index}/{total}) {article.source} | {article.title_original[:60]}"
        )
        try:
            rewrite = client.rewrite(article)
        except ChatGPTRewriteError as exc:
            raise PipelineError(f"LLM rewrite failed for {article.original_url}: {exc}") from exc
        rewrites.append(rewrite)
    print("[pipeline] Completed rewrites.")
    return articles, rewrites


def fetch_rewrite_and_store(
    api: SupportedAPI,
    query: str,
    *,
    artist: str,
    limit: int,
    model: str = "gpt-5-mini",
) -> list[RewriteResult]:
    """Fetch new articles, rewrite them, and persist results to the database."""

    print(
        f"[pipeline] Fetching up to {limit} '{api}' results for artist '{artist}' and query '{query}'..."
    )
    articles = _fetch_articles(api, query, artist=artist, limit=limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return []

    try:
        with get_connection() as conn:
            ensure_article_table(conn)

            client = ChatGPTClient(model=model)
            total = min(len(articles), limit)
            stored: list[RewriteResult] = []

            for index, article in enumerate(articles[:limit], start=1):
                preview = article.title_original[:60]
                print(f"[pipeline] ({index}/{total}) Checking {article.source} | {preview}")

                final_url, is_alive = resolve_final_url(article.original_url)
                final_url_to_store = (
                    final_url if final_url and final_url != article.original_url else None
                )
                urls_to_check = [article.original_url]
                if final_url:
                    urls_to_check.append(final_url)

                with conn.cursor() as cur:
                    cur.execute(
                        'SELECT 1 FROM "Article" WHERE "originalUrl" = ANY(%s) OR "finalUrl" = ANY(%s) LIMIT 1',
                        (urls_to_check, urls_to_check),
                    )
                    exists = cur.fetchone() is not None

                if exists:
                    print("[pipeline]    -> Already stored (URL match), skipping.")
                    continue

                if not is_alive:
                    print("[pipeline]    -> URL unreachable; will mark as disabled.")

                try:
                    rewrite = client.rewrite(article)
                except ChatGPTRewriteError as exc:
                    raise PipelineError(
                        f"LLM rewrite failed for {article.original_url}: {exc}"
                    ) from exc

                enabled = bool(rewrite["relevant"]) and is_alive
                now = datetime.now(timezone.utc)
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO "Article" (
                                "id",
                                "enabled",
                                "originalUrl",
                                "finalUrl",
                                "title",
                                "titleRaw",
                                "publishedAt",
                                "api",
                                "category",
                                "source",
                                "summary",
                                "viewCount",
                                "externalClickCount",
                                "createdAt",
                                "updatedAt"
                            ) VALUES (
                                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                            )
                            """,
                            (
                                uuid.uuid4().hex,
                                enabled,
                                article.original_url,
                                final_url_to_store,
                                rewrite["title"] or None,
                                rewrite["titleRaw"],
                                article.published_at,
                                article.api,
                                article.category,
                                article.source,
                                rewrite["summary"] or None,
                                0,
                                0,
                                now,
                                now,
                            ),
                        )
                    conn.commit()
                except psycopg.Error as exc:
                    conn.rollback()
                    raise PipelineError(
                        f"Failed to insert article {article.original_url}: {exc}"
                    ) from exc
                stored.append(RewriteResult(article=article, rewrite=rewrite))

            skipped = total - len(stored)
            print(
                f"[pipeline] Completed. Stored {len(stored)} new articles, skipped {skipped} duplicates."
            )
            return stored
    except DatabaseError as exc:
        raise PipelineError(str(exc)) from exc
