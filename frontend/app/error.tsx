'use client';

import { useEffect } from 'react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('[App Error]', error);
  }, [error]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div
        className="max-w-md w-full p-8 rounded-2xl border text-center"
        style={{
          background: 'rgba(248, 81, 73, 0.05)',
          borderColor: 'rgba(248, 81, 73, 0.15)',
        }}
      >
        <div className="text-5xl mb-4">⚠️</div>
        <h2 className="text-xl font-bold mb-2" style={{ color: '#e6edf3' }}>
          Something went wrong
        </h2>
        <p className="text-sm mb-6" style={{ color: '#8b949e' }}>
          {error.message || 'An unexpected error occurred.'}
        </p>
        <button
          onClick={reset}
          className="px-6 py-2.5 rounded-lg font-medium text-sm transition-all hover:scale-105"
          style={{
            background: 'linear-gradient(135deg, #3b6fff 0%, #58a6ff 100%)',
            color: '#fff',
            boxShadow: '0 4px 15px rgba(59, 111, 255, 0.3)',
          }}
        >
          Try again
        </button>
      </div>
    </div>
  );
}
