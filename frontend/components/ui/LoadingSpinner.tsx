'use client';

import { cn } from '@/lib/utils';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  text?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4 border-2',
  md: 'w-6 h-6 border-2',
  lg: 'w-8 h-8 border-3',
  xl: 'w-12 h-12 border-4',
};

export function LoadingSpinner({ size = 'md', className, text }: LoadingSpinnerProps) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-3', className)}>
      <div
        className={cn(
          'rounded-full border-blue-500 border-t-transparent animate-spin',
          sizeClasses[size]
        )}
      />
      {text && <span className="text-slate-400 text-sm">{text}</span>}
    </div>
  );
}

export function PageLoader() {
  return (
    <div className="h-full flex items-center justify-center">
      <LoadingSpinner size="xl" text="Loading..." />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl animate-pulse">
      <div className="flex items-start gap-3 mb-4">
        <div className="w-12 h-12 bg-slate-800 rounded-xl" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-800 rounded w-24" />
          <div className="h-3 bg-slate-800 rounded w-32" />
        </div>
      </div>
      <div className="space-y-2">
        <div className="h-3 bg-slate-800 rounded" />
        <div className="h-3 bg-slate-800 rounded w-3/4" />
      </div>
    </div>
  );
}

export function SkeletonText({ lines = 3 }: { lines?: number }) {
  return (
    <div className="space-y-2 animate-pulse">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-4 bg-slate-800 rounded"
          style={{ width: i === lines - 1 ? '75%' : '100%' }}
        />
      ))}
    </div>
  );
}
