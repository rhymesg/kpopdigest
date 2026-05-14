import { NextRequest, NextResponse } from 'next/server';

import { isAdminAuthenticated } from '@/lib/adminAuth';
import { pool } from '@/lib/db';

interface RouteContext {
  params: { id: string };
}

export async function DELETE(req: NextRequest, { params }: RouteContext) {
  if (!isAdminAuthenticated(req.cookies)) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const client = await pool.connect();
  try {
    const result = await client.query(
      `
      UPDATE "Article"
      SET "enabled" = FALSE,
          "updatedAt" = CURRENT_TIMESTAMP
      WHERE "id" = $1
    `,
      [params.id],
    );

    if (result.rowCount === 0) {
      return NextResponse.json({ error: 'Article not found' }, { status: 404 });
    }

    return NextResponse.json({ ok: true });
  } finally {
    client.release();
  }
}
