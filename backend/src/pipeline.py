"""End-to-end helpers to fetch articles, rewrite them, and persist results."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import uuid
from typing import Literal, Sequence, Tuple

import psycopg

from .artist_registry import ArtistDefinition, get_artist_definition, list_registered_artists
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
from .llm_models import ChatGPTRewriteOutput, ChatGPTRSSRewriteOutput
from .naver_blog_api import fetch_naver_blog_posts
from .naver_news_api import fetch_naver_news
from .korea_herald_rss import RSSFetchError, fetch_korea_herald_rss
from .url_utils import resolve_final_url, is_url_blocked

PerArtistAPI = Literal["naver_news", "naver_blog", "daum"]
SupportedAPI = Literal["naver_news", "naver_blog", "daum", "korea_herald_rss"]

DEFAULT_MODEL = "gpt-5-nano"


class PipelineError(RuntimeError):
    """Raised when the fetch → rewrite pipeline fails."""


@dataclass(slots=True)
class RewriteResult:
    article: ArticleOriginal
    rewrite: ChatGPTRewriteOutput


@dataclass(slots=True)
class RSSRewriteResult:
    article: ArticleOriginal
    rewrite: ChatGPTRSSRewriteOutput


def _resolve_artist(artist: str) -> ArtistDefinition:
    try:
        return get_artist_definition(artist)
    except KeyError as exc:
        raise PipelineError(
            f"Unknown artist '{artist}'. Update backend/src/artist_registry.py to register it."
        ) from exc


def _fetch_articles(
    api: PerArtistAPI,
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


def _fetch_rss_articles(limit: int) -> list[ArticleOriginal]:
    if limit <= 0:
        return []
    try:
        return fetch_korea_herald_rss(limit=limit)
    except RSSFetchError as exc:
        raise PipelineError(str(exc)) from exc


def fetch_and_rewrite(
    api: PerArtistAPI,
    *,
    artist: str,
    limit: int,
    model: str = DEFAULT_MODEL,
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
    api: PerArtistAPI,
    *,
    artist: str,
    limit: int,
    model: str = DEFAULT_MODEL,
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

                # Check if URL is blocked
                urls_to_check_for_blocking = [article.original_url]
                if final_url:
                    urls_to_check_for_blocking.append(final_url)
                
                is_blocked = any(is_url_blocked(url) for url in urls_to_check_for_blocking)
                if is_blocked:
                    disabled_reason = disabled_reason or "blocked_url_pattern"

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

                enabled = bool(rewrite["relevant"]) and is_alive and not is_blocked
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


def fetch_rss_and_rewrite(
    *,
    limit: int,
    model: str = DEFAULT_MODEL,
) -> Tuple[Sequence[ArticleOriginal], Sequence[ChatGPTRSSRewriteOutput]]:
    """Fetch Korea Herald RSS articles and rewrite them via ChatGPT."""

    print(f"[pipeline] Fetching up to {limit} 'korea_herald_rss' results...")
    articles = _fetch_rss_articles(limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return articles, []

    candidate_artists = list_registered_artists()
    client = ChatGPTClient(model=model)
    rewrites: list[ChatGPTRSSRewriteOutput] = []
    total = min(len(articles), limit)
    print(f"[pipeline] Running RSS rewrites with model '{model}'...")
    for index, article in enumerate(articles[:limit], start=1):
        preview = article.title_original[:60]
        print(f"[pipeline] ({index}/{total}) {article.source} | {preview}")
        try:
            rewrite = client.rewrite_rss(
                article,
                candidate_artists=candidate_artists,
            )
        except ChatGPTRewriteError as exc:
            raise PipelineError(
                f"LLM rewrite failed for {article.original_url}: {exc}"
            ) from exc
        rewrites.append(rewrite)
    print("[pipeline] Completed RSS rewrites.")
    return articles, rewrites


def fetch_rss_rewrite_and_store(
    *,
    limit: int,
    model: str = DEFAULT_MODEL,
) -> list[RSSRewriteResult]:
    """Fetch RSS articles, run rewrites, and persist results to the database."""

    print(f"[pipeline] Fetching up to {limit} 'korea_herald_rss' results...")
    articles = _fetch_rss_articles(limit)
    print(f"[pipeline] Retrieved {len(articles)} articles.")
    if not articles:
        return []

    candidate_names = list_registered_artists()
    definition_cache = {
        name: get_artist_definition(name)
        for name in candidate_names
    }

    try:
        with get_connection() as conn:
            ensure_schema(conn)

            client = ChatGPTClient(model=model)
            total = min(len(articles), limit)
            stored: list[RSSRewriteResult] = []
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

                existing_article_id: str | None = None
                with conn.cursor() as cur:
                    cur.execute(
                        'SELECT "id" FROM "Article" WHERE "originalUrl" = ANY(%s) OR "finalUrl" = ANY(%s) LIMIT 1',
                        (urls_to_check, urls_to_check),
                    )
                    row = cur.fetchone()
                    if row:
                        existing_article_id = row[0]

                try:
                    rewrite = client.rewrite_rss(
                        article,
                        candidate_artists=candidate_names,
                    )
                except ChatGPTRewriteError as exc:
                    print(
                        f"[pipeline]    -> LLM rewrite failed: {exc}. Skipping article.",
                        flush=True,
                    )
                    continue

                artist_definitions = [
                    definition_cache[name]
                    for name in rewrite["artists"]
                    if name in definition_cache
                ]

                disabled_reason: str | None = None
                if not is_alive:
                    disabled_reason = "unreachable"

                urls_to_check_for_blocking = [article.original_url]
                if final_url:
                    urls_to_check_for_blocking.append(final_url)

                is_blocked = any(is_url_blocked(url) for url in urls_to_check_for_blocking)
                if is_blocked:
                    disabled_reason = disabled_reason or "blocked_url_pattern"

                if not rewrite["relevant"]:
                    disabled_reason = disabled_reason or "irrelevant"

                if existing_article_id:
                    created_links = 0
                    performed_work = False
                    try:
                        for definition in artist_definitions:
                            artist_id = get_or_create_artist(
                                conn,
                                name=definition.display_name,
                                slug=definition.slug,
                            )
                            performed_work = True
                            if link_article_to_artist(
                                conn, article_id=existing_article_id, artist_id=artist_id
                            ):
                                created_links += 1
                        if performed_work:
                            conn.commit()
                        if created_links:
                            linked_existing += 1
                            print(
                                "[pipeline]    -> Already stored, linked to artists."
                            )
                    except psycopg.Error as exc:
                        conn.rollback()
                        raise PipelineError(
                            f"Failed to link existing article {article.original_url}: {exc}"
                        ) from exc
                    continue

                enabled = bool(rewrite["relevant"]) and is_alive and not is_blocked
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

                    for definition in artist_definitions:
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

                stored.append(RSSRewriteResult(article=article, rewrite=rewrite))
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
