import { createHmac, timingSafeEqual } from 'crypto';

export const ADMIN_COOKIE_NAME = 'kpd_admin_session';

const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;
const SESSION_VERSION = 'v1';

type CookieReader = {
  get(name: string): { value: string } | undefined;
};

const getAdminPassword = () => process.env.ADMIN_PASSWORD ?? '';
const getSessionSecret = () => process.env.ADMIN_SESSION_SECRET ?? '';

function signPayload(payload: string) {
  return createHmac('sha256', getSessionSecret()).update(payload).digest('hex');
}

function safeEqual(left: string, right: string) {
  const leftBuffer = Buffer.from(left);
  const rightBuffer = Buffer.from(right);
  if (leftBuffer.length !== rightBuffer.length) return false;
  return timingSafeEqual(leftBuffer, rightBuffer);
}

export function verifyAdminPassword(password: string) {
  const expected = getAdminPassword();
  if (!expected) return false;
  return safeEqual(password, expected);
}

export function createAdminSessionCookieValue(now = Date.now()) {
  if (!getSessionSecret()) {
    throw new Error('ADMIN_SESSION_SECRET is required for admin login.');
  }
  const expiresAt = now + SESSION_MAX_AGE_SECONDS * 1000;
  const payload = `${SESSION_VERSION}.${expiresAt}`;
  return `${payload}.${signPayload(payload)}`;
}

export function verifyAdminSessionCookieValue(value?: string) {
  if (!value || !getSessionSecret()) return false;

  const parts = value.split('.');
  if (parts.length !== 3) return false;

  const [version, expiresAtRaw, signature] = parts;
  if (version !== SESSION_VERSION) return false;

  const expiresAt = Number(expiresAtRaw);
  if (!Number.isFinite(expiresAt) || expiresAt <= Date.now()) return false;

  const payload = `${version}.${expiresAtRaw}`;
  return safeEqual(signature, signPayload(payload));
}

export function isAdminAuthenticated(cookieStore: CookieReader) {
  return verifyAdminSessionCookieValue(cookieStore.get(ADMIN_COOKIE_NAME)?.value);
}

export const adminCookieOptions = {
  httpOnly: true,
  sameSite: 'lax' as const,
  secure: process.env.NODE_ENV === 'production',
  path: '/',
  maxAge: SESSION_MAX_AGE_SECONDS,
};
