import type { ArticleCategory } from './categories';
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
  category: string;
  likeCount: number;
}

export type ArticleBadge = 'dailyBest' | 'weeklyBest';

export type ArticleWithBadges = ArticleRow & { badges?: ArticleBadge[] };

type FetchArticlesOptions = {
  limit: number;
  offset?: number;
  artistSlug?: string;
  category?: ArticleCategory;
  search?: string;
};

export async function fetchArticles(options: FetchArticlesOptions): Promise<ArticleRow[]> {
  const { limit, offset = 0, artistSlug, category, search } = options;
  const client = await pool.connect();
  try {
    const params: unknown[] = [limit, offset];
    let result;
    if (artistSlug) {
      params.push(artistSlug);
      let whereClause = 'a."enabled" = TRUE AND ar."slug" = $3';
      if (category) {
        params.push(category);
        whereClause += ` AND a."category" = $${params.length}`;
      }
      if (search) {
        params.push(`%${search}%`);
        whereClause += (
          ` AND (a."title" ILIKE $${params.length}` +
          ` OR a."titleRaw" ILIKE $${params.length}` +
          ` OR a."summary" ILIKE $${params.length}` +
          ` OR a."source" ILIKE $${params.length})`
        );
      }
      result = await client.query(
        `
        SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
               a."publishedAt", a."source", a."api", a."category", a."likeCount",
               ar."slug" AS "artist"
        FROM "Article" a
        JOIN "ArticleArtist" aa ON aa."articleId" = a."id"
        JOIN "Artist" ar ON ar."id" = aa."artistId"
        WHERE ${whereClause}
        ORDER BY a."publishedAt" DESC
        LIMIT $1 OFFSET $2
      `,
        params,
      );
    } else {
      let whereClause = 'a."enabled" = TRUE';
      if (category) {
        params.push(category);
        whereClause += ` AND a."category" = $${params.length}`;
      }
      if (search) {
        params.push(`%${search}%`);
        whereClause += (
          ` AND (a."title" ILIKE $${params.length}` +
          ` OR a."titleRaw" ILIKE $${params.length}` +
          ` OR a."summary" ILIKE $${params.length}` +
          ` OR a."source" ILIKE $${params.length})`
        );
      }
      result = await client.query(
        `
        SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
               a."publishedAt", a."source", a."api", a."category", a."likeCount",
               (
                 SELECT STRING_AGG(ar."slug", ',')
                 FROM "ArticleArtist" aa
                 JOIN "Artist" ar ON ar."id" = aa."artistId"
                 WHERE aa."articleId" = a."id"
               ) AS "artist"
        FROM "Article" a
        WHERE ${whereClause}
        ORDER BY a."publishedAt" DESC
        LIMIT $1 OFFSET $2
      `,
        params,
      );
    }
    return result.rows.map((row) => {
      return mapRowToArticle(row);
    });
  } finally {
    client.release();
  }
}

type HighlightedArticlesOptions = Omit<FetchArticlesOptions, 'offset'>;

export async function fetchArticlesWithHighlights(
  options: HighlightedArticlesOptions,
): Promise<{ featuredArticles: ArticleWithBadges[]; articles: ArticleRow[] }> {
  const { limit, artistSlug, category, search } = options;
  const { daily, weekly } = await fetchBestArticles({ artistSlug, category, search });

  const featuredMap = new Map<string, ArticleWithBadges>();
  if (daily) {
    featuredMap.set(daily.id, { ...daily, badges: ['dailyBest'] });
  }
  if (weekly) {
    const existing = featuredMap.get(weekly.id);
    if (existing) {
      const mergedBadges = new Set(existing.badges ?? []);
      mergedBadges.add('weeklyBest');
      featuredMap.set(weekly.id, { ...existing, badges: Array.from(mergedBadges) as ArticleBadge[] });
    } else {
      featuredMap.set(weekly.id, { ...weekly, badges: ['weeklyBest'] });
    }
  }
  const featuredArticles = Array.from(featuredMap.values());
  const extraRequired = featuredArticles.length;

  const articles = await fetchArticles({
    limit: limit + extraRequired,
    offset: 0,
    artistSlug,
    category,
    search,
  });

  const featuredIds = new Set(featuredArticles.map((article) => article.id));
  const regularArticles = articles.filter((article) => !featuredIds.has(article.id)).slice(0, limit);

  return { featuredArticles, articles: regularArticles };
}

type BestArticleParams = {
  artistSlug?: string;
  category?: ArticleCategory;
  search?: string;
};

const BEST_WINDOWS: Record<'daily' | 'weekly', string> = {
  daily: "INTERVAL '24 hours'",
  weekly: "INTERVAL '7 days'",
};

export async function fetchBestArticles(
  params: BestArticleParams,
): Promise<{ daily?: ArticleRow; weekly?: ArticleRow }> {
  const [daily, weekly] = await Promise.all([
    fetchBestArticleForWindow('daily', params),
    fetchBestArticleForWindow('weekly', params),
  ]);
  return { daily: daily ?? undefined, weekly: weekly ?? undefined };
}

async function fetchBestArticleForWindow(
  windowKey: keyof typeof BEST_WINDOWS,
  filters: BestArticleParams,
): Promise<ArticleRow | null> {
  const client = await pool.connect();
  try {
    const params: unknown[] = [];
    let whereClause = 'a."enabled" = TRUE';
    whereClause += ` AND a."publishedAt" >= NOW() - ${BEST_WINDOWS[windowKey]}`;

    if (filters.category) {
      params.push(filters.category);
      whereClause += ` AND a."category" = $${params.length}`;
    }
    if (filters.search) {
      params.push(`%${filters.search}%`);
      whereClause += (
        ` AND (a."title" ILIKE $${params.length}` +
        ` OR a."titleRaw" ILIKE $${params.length}` +
        ` OR a."summary" ILIKE $${params.length}` +
        ` OR a."source" ILIKE $${params.length})`
      );
    }

    if (filters.artistSlug) {
      params.push(filters.artistSlug);
      const slugParamIndex = params.length;
      const result = await client.query(
        `
        SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
               a."publishedAt", a."source", a."api", a."category", a."likeCount",
               ar."slug" AS "artist"
        FROM "Article" a
        JOIN "ArticleArtist" aa ON aa."articleId" = a."id"
        JOIN "Artist" ar ON ar."id" = aa."artistId"
        WHERE ${whereClause} AND ar."slug" = $${slugParamIndex}
        ORDER BY a."likeCount" DESC, a."publishedAt" DESC
        LIMIT 1
      `,
        params,
      );
      if (result.rows.length === 0) {
        return null;
      }
      return mapRowToArticle(result.rows[0]);
    }

    const result = await client.query(
      `
      SELECT a."id", a."title", a."titleRaw", a."summary", a."originalUrl", a."finalUrl",
             a."publishedAt", a."source", a."api", a."category", a."likeCount",
             (
               SELECT STRING_AGG(ar."slug", ',')
               FROM "ArticleArtist" aa
               JOIN "Artist" ar ON ar."id" = aa."artistId"
               WHERE aa."articleId" = a."id"
             ) AS "artist"
      FROM "Article" a
      WHERE ${whereClause}
      ORDER BY a."likeCount" DESC, a."publishedAt" DESC
      LIMIT 1
    `,
      params,
    );
    if (result.rows.length === 0) {
      return null;
    }
    return mapRowToArticle(result.rows[0]);
  } finally {
    client.release();
  }
}

function mapRowToArticle(row: Record<string, unknown>): ArticleRow {
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
    category,
    likeCount,
  } = row as {
    id: string;
    title: string | null;
    titleRaw: string;
    summary: string | null;
    originalUrl: string;
    finalUrl: string | null;
    publishedAt: Date | string;
    source: string;
    api: string;
    artist: string;
    category: string;
    likeCount: number | string | null;
  };

  const published = publishedAt instanceof Date ? publishedAt : new Date(publishedAt);
  const normalizedPublishedAt = Number.isNaN(published.getTime())
    ? null
    : published.toISOString();
  const normalizedLikeCount = Number(likeCount ?? 0);

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
    category,
    likeCount: Number.isNaN(normalizedLikeCount) ? 0 : normalizedLikeCount,
  } satisfies ArticleRow;
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
