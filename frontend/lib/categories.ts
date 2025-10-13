export const ARTICLE_CATEGORIES = ['news', 'blog', 'community'] as const;

export type ArticleCategory = (typeof ARTICLE_CATEGORIES)[number];

export function normalizeCategory(value: string | null | undefined): ArticleCategory | undefined {
  if (!value) return undefined;
  const lower = value.toLowerCase();
  if ((ARTICLE_CATEGORIES as readonly string[]).includes(lower)) {
    return lower as ArticleCategory;
  }
  return undefined;
}
