import { NextRequest, NextResponse } from 'next/server';

import { fetchArticles } from '@/lib/articles';
import { normalizeCategory } from '@/lib/categories';
import { DEFAULT_PAGE_SIZE } from '@/lib/constants';

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const offset = Number(searchParams.get('offset') ?? '0');
  const limit = Number(searchParams.get('limit') ?? DEFAULT_PAGE_SIZE);
  const slug = searchParams.get('slug') ?? undefined;
  const category = normalizeCategory(searchParams.get('category'));
  const searchRaw = searchParams.get('search');
  const search = searchRaw && searchRaw.trim() ? searchRaw.trim() : undefined;

  const articles = await fetchArticles({
    limit,
    offset,
    artistSlug: slug,
    category,
    search,
  });

  return NextResponse.json({
    articles,
    hasMore: articles.length === limit,
  });
}
