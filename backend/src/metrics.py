"""Helpers for reading artist metrics."""

from __future__ import annotations

from typing import List, Tuple

import psycopg

from .db import DATABASE_URL_ENV


def fetch_artist_metrics() -> List[Tuple[str, str, int]]:
    """Return [(slug, name, page_views), ...] ordered by page_views desc."""

    import os

    connection_string = os.getenv(DATABASE_URL_ENV)
    if not connection_string:
        raise RuntimeError("DATABASE_URL must be set.")

    with psycopg.connect(connection_string) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT ar."slug", ar."name", COALESCE(am."pageViews", 0) AS views
            FROM "Artist" ar
            LEFT JOIN "ArtistMetrics" am ON am."artistId" = ar."id"
            ORDER BY views DESC, ar."name" ASC
            """
        )
        return [(row[0], row[1], row[2]) for row in cur.fetchall()]
