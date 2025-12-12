import { NextResponse } from 'next/server';

import { pool } from '@/lib/db';

interface RouteParams {
  params: { id: string };
}

export async function POST(_: Request, { params }: RouteParams) {
  const articleId = params.id;
  if (!articleId) {
    return NextResponse.json({ error: 'Missing article id' }, { status: 400 });
  }

  const client = await pool.connect();
  try {
    const result = await client.query(
      `
      UPDATE "Article"
      SET "likeCount" = "likeCount" + 1,
          "updatedAt" = CURRENT_TIMESTAMP
      WHERE "id" = $1
      RETURNING "likeCount"
    `,
      [articleId],
    );

    if (result.rowCount === 0) {
      return NextResponse.json({ error: 'Article not found' }, { status: 404 });
    }

    const nextCountRaw = result.rows[0]?.likeCount ?? 0;
    const nextCount = Number(nextCountRaw);

    return NextResponse.json({ likeCount: Number.isNaN(nextCount) ? 0 : nextCount });
  } catch (error) {
    console.error('Failed to increment like count', error);
    return NextResponse.json({ error: 'Failed to like article' }, { status: 500 });
  } finally {
    client.release();
  }
}
