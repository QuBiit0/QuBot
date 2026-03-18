'use client';

import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth.store';
import { PageLoader } from '@/components/ui';

const PUBLIC_ROUTES = ['/login', '/register'];

export function AuthProvider({ children }: { readonly children: React.ReactNode }) {
  const { hydrate, isAuthenticated, isLoading } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    // Run hydration on mount to load tokens and user info
    hydrate();
  }, [hydrate]);

  useEffect(() => {
    if (isLoading) return;

    if (!isAuthenticated && !PUBLIC_ROUTES.includes(pathname)) {
      router.push('/login');
    } else if (isAuthenticated && PUBLIC_ROUTES.includes(pathname)) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, isLoading, pathname, router]);

  // Optionally show a full-screen loading state until hydrated
  if (isLoading) {
    return <PageLoader />;
  }

  // Prevent flash of protected content
  if (!isAuthenticated && !PUBLIC_ROUTES.includes(pathname)) {
    return <PageLoader />;
  }

  return <>{children}</>;
}
