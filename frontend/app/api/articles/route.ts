import { NextRequest, NextResponse } from 'next/server';

import { fetchArticles } from '@/lib/articles';

const DEFAULT_LIMIT = 20;

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const offset = Number(searchParams.get('offset') ?? '0');
  const limit = Number(searchParams.get('limit') ?? DEFAULT_LIMIT);
  const slug = searchParams.get('slug') ?? undefined;

  const articles = await fetchArticles({
    limit,
    offset,
    artistSlug: slug,
  });

  return NextResponse.json({
    articles,
    hasMore: articles.length === limit,
  });
}
