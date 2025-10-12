"""End-to-end helpers to fetch articles, rewrite them, and persist results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from typing import Literal, Sequence, Tuple

import psycopg

from .artist_registry import ArtistDefinition, get_artist_definition
from .article_models import ArticleOriginal
from .chatgpt_client import ChatGPTClient, ChatGPTRewriteError
from .daum_api import fetch_daum_web
from .db import (
    DatabaseError,
    ensure_schema,
    get_connection,
    get_or_create_artist,
    link_article_to_artist,
)
from .llm_models import ChatGPTRewriteOutput
from .naver_blog_api import fetch_naver_blog_posts
from .naver_news_api import fetch_naver_news
from .url_utils import resolve_final_url

SupportedAPI = Literal["naver_news", "naver_blog", "daum"]


class PipelineError(RuntimeError):
    """Raised when the fetch → rewrite pipeline fails."""


@dataclass(slots=True)
class RewriteResult:
    article: ArticleOriginal
    rewrite: ChatGPTRewriteOutput


def _resolve_artist(artist: str) -> ArtistDefinition:
    try:
        return get_artist_definition(artist)
    except KeyError as exc:
        raise PipelineError(
            f"Unknown artist '{artist}'. Update backend/src/artist_registry.py to register it."
        ) from exc


def _fetch_articles(
    api: SupportedAPI,
    *,
    definition: ArtistDefinition,
    limit: int,
) -> list[ArticleOriginal]:
    query = definition.search_query
    if limit <= 0:
        return []

    if api == "naver_news":
        return fetch_naver_news(
            query,
            artist=definition.display_name,
            display=limit,
        )[:limit]

    if api == "naver_blog":
        return fetch_naver_blog_posts(
            query,
            artist=definition.display_name,
            display=limit,
        )[:limit]
    if api == "daum":
        return fetch_daum_web(query, artist=definition.display_name, size=limit)[:limit]

    raise PipelineError(f"Unsupported API: {api}")


def fetch_and_rewrite(
    api: SupportedAPI,
    *,
    artist: str,
    limit: int,
    model: str = "gpt-5-mini",
) -> Tuple[Sequence[ArticleOriginal], Sequence[ChatGPTRewriteOutput]]:
    """Fetch articles from the chosen API and rewrite them via ChatGPT."""

    definition = _resolve_artist(artist)
    print(
        f"[pipeline] Fetching up to {limit} '{api}' results for artist '{definition.display_name}' "
        f"(query: {definition.search_query})..."
    )
    articles = _fetch_articles(api, definition=definition, limit=limit)
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
    *,
    artist: str,
    limit: int,
    model: str = "gpt-5-mini",
) -> list[RewriteResult]:
    """Fetch new articles, rewrite them, and persist results to the database."""

    definition = _resolve_artist(artist)
    print(
        f"[pipeline] Fetching up to {limit} '{api}' results for artist '{definition.display_name}' "
        f"(query: {definition.search_query})..."
    )
    articles = _fetch_articles(api, definition=definition, limit=limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return []

    try:
        with get_connection() as conn:
            ensure_schema(conn)

            client = ChatGPTClient(model=model)
            total = min(len(articles), limit)
            stored: list[RewriteResult] = []
            linked_existing = 0
            enabled_count = 0

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
                        'SELECT "id" FROM "Article" WHERE "originalUrl" = ANY(%s) OR "finalUrl" = ANY(%s) LIMIT 1',
                        (urls_to_check, urls_to_check),
                    )
                    row = cur.fetchone()

                if row:
                    article_id = row[0]
                    try:
                        artist_id = get_or_create_artist(
                            conn,
                            name=definition.display_name,
                            slug=definition.slug,
                        )
                        created = link_article_to_artist(
                            conn, article_id=article_id, artist_id=artist_id
                        )
                        conn.commit()
                    except psycopg.Error as exc:
                        conn.rollback()
                        raise PipelineError(
                            f"Failed to link existing article {article.original_url}: {exc}"
                        ) from exc
                    if created:
                        linked_existing += 1
                        print("[pipeline]    -> Already stored, linked to artist.")
                    continue

                disabled_reason: str | None = None
                if not is_alive:
                    disabled_reason = "unreachable"

                try:
                    rewrite = client.rewrite(article)
                except ChatGPTRewriteError as exc:
                    print(
                        f"[pipeline]    -> LLM rewrite failed: {exc}. Skipping article.",
                        flush=True,
                    )
                    continue

                if not rewrite["relevant"]:
                    disabled_reason = disabled_reason or "irrelevant"

                enabled = bool(rewrite["relevant"]) and is_alive
                now = datetime.now(timezone.utc)
                try:
                    article_id = uuid.uuid4().hex
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
                                article_id,
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
                    artist_id = get_or_create_artist(
                        conn,
                        name=definition.display_name,
                        slug=definition.slug,
                    )
                    link_article_to_artist(
                        conn, article_id=article_id, artist_id=artist_id
                    )
                    conn.commit()
                except psycopg.Error as exc:
                    conn.rollback()
                    raise PipelineError(
                        f"Failed to insert article {article.original_url}: {exc}"
                    ) from exc
                stored.append(RewriteResult(article=article, rewrite=rewrite))
                if enabled:
                    enabled_count += 1
                elif disabled_reason:
                    print(f"[pipeline]    -> Disabled: ({disabled_reason}).")

            skipped = max(total - len(stored) - linked_existing, 0)
            print(
                f"[pipeline] Completed. Stored {len(stored)} new articles ({enabled_count} enabled), "
                f"linked {linked_existing} existing, skipped {skipped} duplicates."
            )
            return stored
    except DatabaseError as exc:
        raise PipelineError(str(exc)) from exc
