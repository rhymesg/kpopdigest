"""Database helpers for storing articles."""

from __future__ import annotations

import os
from contextlib import contextmanager

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


def ensure_article_table(conn: psycopg.Connection) -> None:
    """Create the Article table if it does not already exist."""

    ddl = """
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
    """
    with conn.cursor() as cur:
        cur.execute(ddl)
        conn.commit()
