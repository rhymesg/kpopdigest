import { pool } from './db';

export interface ArticleRow {
  id: string;
  title: string | null;
  titleRaw: string;
  summary: string | null;
  originalUrl: string;
  finalUrl: string | null;
  publishedAt: string;
  source: string;
  api: string;
  artist: string;
}

export async function fetchArticles(options: {
  limit: number;
  offset?: number;
  artistSlug?: string;
}): Promise<ArticleRow[]> {
  const { limit, offset = 0, artistSlug } = options;
  const client = await pool.connect();
  try {
    const params: unknown[] = [limit, offset];
    let result;
    if (artistSlug) {
      params.push(artistSlug);
      result = await client.query(
        `
        SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
               a."publishedAt", a."source", a."api", ar."slug" AS "artist"
        FROM "Article" a
        JOIN "ArticleArtist" aa ON aa."articleId" = a."id"
        JOIN "Artist" ar ON ar."id" = aa."artistId"
        WHERE a."enabled" = TRUE AND ar."slug" = $3
        ORDER BY a."publishedAt" DESC
        LIMIT $1 OFFSET $2
      `,
        params,
      );
    } else {
      result = await client.query(
        `
        SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
               a."publishedAt", a."source", a."api",
               (
                 SELECT STRING_AGG(ar."slug", ',')
                 FROM "ArticleArtist" aa
                 JOIN "Artist" ar ON ar."id" = aa."artistId"
                 WHERE aa."articleId" = a."id"
               ) AS "artist"
        FROM "Article" a
        WHERE a."enabled" = TRUE
        ORDER BY a."publishedAt" DESC
        LIMIT $1 OFFSET $2
      `,
        params,
      );
    }
    return result.rows.map((row) => {
      const {
        id,
        title,
        titleRaw,
        summary,
        originalUrl,
        finalUrl,
        publishedAt,
        source,
        api,
        artist,
      } = row;

      const published = publishedAt instanceof Date ? publishedAt : new Date(publishedAt);
      const normalizedPublishedAt = Number.isNaN(published.getTime())
        ? null
        : published.toISOString();

      return {
        id,
        title,
        titleRaw,
        summary,
        originalUrl,
        finalUrl,
        publishedAt: normalizedPublishedAt ?? String(publishedAt ?? ''),
        source,
        api,
        artist,
      } satisfies ArticleRow;
    });
  } finally {
    client.release();
  }
}

export async function countArticles(artistSlug?: string): Promise<number> {
  const client = await pool.connect();
  try {
    if (artistSlug) {
      const result = await client.query(
        `
        SELECT COUNT(*) AS count
        FROM "Article" a
        JOIN "ArticleArtist" aa ON aa."articleId" = a."id"
        JOIN "Artist" ar ON ar."id" = aa."artistId"
        WHERE a."enabled" = TRUE AND ar."slug" = $1
      `,
        [artistSlug],
      );
      return Number(result.rows[0]?.count ?? 0);
    }

    const result = await client.query(
      'SELECT COUNT(*) AS count FROM "Article" WHERE "enabled" = TRUE'
    );
    return Number(result.rows[0]?.count ?? 0);
  } finally {
    client.release();
  }
}
