import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950">
      <div className="text-center">
        <div
          className="text-[120px] font-black leading-none mb-4"
          style={{
            background: 'linear-gradient(135deg, #3b6fff, #a371f7)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          404
        </div>
        <h2 className="text-2xl font-bold mb-2" style={{ color: '#e6edf3' }}>
          Page not found
        </h2>
        <p className="text-sm mb-8" style={{ color: '#6e7681' }}>
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link
          href="/dashboard"
          className="px-6 py-2.5 rounded-lg font-medium text-sm"
          style={{
            background: 'linear-gradient(135deg, #3b6fff 0%, #58a6ff 100%)',
            color: '#fff',
          }}
        >
          Back to Dashboard
        </Link>
      </div>
    </div>
  );
}
