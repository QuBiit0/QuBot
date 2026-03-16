'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/store/auth.store';
import Link from 'next/link';

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading, error, clearError } = useAuthStore();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();

    try {
      await login({ email, password });
      router.push('/dashboard');
    } catch {
      // Error is already set in the store
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      {/* Background effects */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: `
            radial-gradient(ellipse at 30% 20%, rgba(59, 111, 255, 0.08) 0%, transparent 50%),
            radial-gradient(ellipse at 70% 80%, rgba(163, 113, 247, 0.06) 0%, transparent 50%)
          `,
        }}
      />

      <div
        className="relative w-full max-w-md rounded-2xl p-8 border"
        style={{
          background: 'rgba(13, 17, 28, 0.8)',
          backdropFilter: 'blur(20px)',
          borderColor: 'rgba(255, 255, 255, 0.06)',
        }}
      >
        {/* Logo */}
        <div className="text-center mb-8">
          <div
            className="w-14 h-14 rounded-2xl mx-auto mb-4 flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(59, 111, 255, 0.2), rgba(163, 113, 247, 0.2))',
              border: '1px solid rgba(59, 111, 255, 0.3)',
            }}
          >
            <span className="text-2xl font-bold" style={{ color: '#3b6fff' }}>
              Q
            </span>
          </div>
          <h1 className="text-2xl font-bold" style={{ color: '#e6edf3' }}>
            Welcome back
          </h1>
          <p className="text-sm mt-1" style={{ color: '#6e7681' }}>
            Sign in to Qubot Mission Control
          </p>
        </div>

        {/* Error */}
        {error && (
          <div
            className="mb-4 px-4 py-3 rounded-lg text-sm"
            style={{
              background: 'rgba(248, 81, 73, 0.1)',
              border: '1px solid rgba(248, 81, 73, 0.2)',
              color: '#f85149',
            }}
          >
            {error}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label
              htmlFor="email"
              className="block text-xs font-medium mb-1.5"
              style={{ color: '#8b949e' }}
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-colors"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: '#e6edf3',
              }}
            />
          </div>

          <div>
            <label
              htmlFor="password"
              className="block text-xs font-medium mb-1.5"
              style={{ color: '#8b949e' }}
            >
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-colors"
              style={{
                background: 'rgba(255, 255, 255, 0.04)',
                border: '1px solid rgba(255, 255, 255, 0.08)',
                color: '#e6edf3',
              }}
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-lg font-medium text-sm transition-all disabled:opacity-50"
            style={{
              background: 'linear-gradient(135deg, #3b6fff 0%, #58a6ff 100%)',
              color: '#fff',
              boxShadow: '0 4px 15px rgba(59, 111, 255, 0.3)',
            }}
          >
            {isLoading ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        {/* Register link */}
        <p className="text-center text-sm mt-6" style={{ color: '#6e7681' }}>
          Don&apos;t have an account?{' '}
          <Link
            href="/register"
            className="font-medium hover:underline"
            style={{ color: '#58a6ff' }}
          >
            Create one
          </Link>
        </p>
      </div>
    </div>
  );
}
