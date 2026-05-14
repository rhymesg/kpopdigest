import { NextRequest, NextResponse } from 'next/server';

import {
  ADMIN_COOKIE_NAME,
  adminCookieOptions,
  createAdminSessionCookieValue,
  verifyAdminPassword,
} from '@/lib/adminAuth';

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  const password = typeof body?.password === 'string' ? body.password : '';

  if (!verifyAdminPassword(password)) {
    return NextResponse.json({ error: 'Invalid password' }, { status: 401 });
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(ADMIN_COOKIE_NAME, createAdminSessionCookieValue(), adminCookieOptions);
  return res;
}
