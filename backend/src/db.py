"""Database helpers for storing articles."""

from __future__ import annotations

import os
from contextlib import contextmanager
import uuid

import psycopg

DATABASE_URL_ENV = "DATABASE_URL"


class DatabaseError(RuntimeError):
    """Raised when database configuration or operations fail."""


@contextmanager
def get_connection():
    """Yield a PostgreSQL connection using the DATABASE_URL environment variable."""

    url = os.getenv(DATABASE_URL_ENV)
    if not url:
        raise DatabaseError(
            "DATABASE_URL is not set. Add it to backend/.env (see .env.example)."
        )
    conn = psycopg.connect(url)
    try:
        yield conn
    finally:
        conn.close()


def ensure_schema(conn: psycopg.Connection) -> None:
    """Create core tables if they do not already exist."""

    ddl_statements = [
        """
        CREATE TABLE IF NOT EXISTS "Article" (
            "id" TEXT PRIMARY KEY,
            "enabled" BOOLEAN NOT NULL DEFAULT TRUE,
            "originalUrl" TEXT NOT NULL UNIQUE,
            "finalUrl" TEXT,
            "title" TEXT,
            "titleRaw" TEXT NOT NULL,
            "publishedAt" TIMESTAMPTZ NOT NULL,
            "api" TEXT NOT NULL,
            "category" TEXT NOT NULL,
            "source" TEXT NOT NULL,
            "summary" TEXT,
            "viewCount" INTEGER NOT NULL DEFAULT 0,
            "externalClickCount" INTEGER NOT NULL DEFAULT 0,
            "createdAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS "Artist" (
            "id" TEXT PRIMARY KEY,
            "name" TEXT NOT NULL UNIQUE,
            "slug" TEXT NOT NULL UNIQUE,
            "createdAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS "ArticleArtist" (
            "id" TEXT PRIMARY KEY,
            "articleId" TEXT NOT NULL REFERENCES "Article"("id") ON DELETE CASCADE,
            "artistId" TEXT NOT NULL REFERENCES "Artist"("id") ON DELETE CASCADE,
            "createdAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE ("articleId", "artistId")
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS "ArtistMetrics" (
            "artistId" TEXT PRIMARY KEY REFERENCES "Artist"("id") ON DELETE CASCADE,
            "pageViews" BIGINT NOT NULL DEFAULT 0,
            "updatedAt" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """,
    ]

    with conn.cursor() as cur:
        for ddl in ddl_statements:
            cur.execute(ddl)
    conn.commit()


def get_or_create_artist(conn: psycopg.Connection, *, name: str, slug: str) -> str:
    """Return an artist id for the given slug, inserting a new row if needed."""

    with conn.cursor() as cur:
        cur.execute('SELECT "id" FROM "Artist" WHERE "slug" = %s', (slug,))
        row = cur.fetchone()
        if row:
            artist_id = row[0]
        else:
            artist_id = uuid.uuid4().hex
            cur.execute(
                'INSERT INTO "Artist" ("id", "name", "slug") VALUES (%s, %s, %s) RETURNING "id"',
                (artist_id, name, slug),
            )
            artist_id = cur.fetchone()[0]

        cur.execute(
            'INSERT INTO "ArtistMetrics" ("artistId") VALUES (%s) ON CONFLICT ("artistId") DO NOTHING',
            (artist_id,),
        )

        return artist_id


def link_article_to_artist(conn: psycopg.Connection, *, article_id: str, artist_id: str) -> bool:
    """Ensure an Article ↔ Artist association exists.

    Returns True if a new link was created, False if it already existed.
    """

    with conn.cursor() as cur:
        cur.execute(
            'INSERT INTO "ArticleArtist" ("id", "articleId", "artistId") VALUES (%s, %s, %s) '
            'ON CONFLICT ("articleId", "artistId") DO NOTHING',
            (uuid.uuid4().hex, article_id, artist_id),
        )
        return cur.rowcount > 0
