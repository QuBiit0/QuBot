'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Sidebar } from '@/components/layout/Sidebar';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex h-screen w-full overflow-hidden">
        <Sidebar />
        <main className="flex-1 min-w-0 h-screen overflow-hidden flex flex-col">
          {children}
        </main>
      </div>
    </QueryClientProvider>
  );
}
