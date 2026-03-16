import { NextRequest, NextResponse } from 'next/server';

const PUBLIC_PATHS = ['/login', '/register'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Allow public paths and Next.js internals
  if (
    PUBLIC_PATHS.some((p) => pathname.startsWith(p)) ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/api') ||
    pathname.includes('.')
  ) {
    return NextResponse.next();
  }

  // Check for token in cookie (set by zustand persist) or Authorization header
  const token =
    request.cookies.get('qubot-auth-storage')?.value ||
    request.headers.get('Authorization');

  // Parse zustand persisted state from cookie
  if (token) {
    try {
      const parsed = JSON.parse(decodeURIComponent(token));
      if (parsed?.state?.token) {
        return NextResponse.next();
      }
    } catch {
      // Not JSON — could be a raw token header, allow through
    }
  }

  // No valid token found — redirect to login
  const loginUrl = new URL('/login', request.url);
  loginUrl.searchParams.set('from', pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|login|register).*)',
  ],
};
