import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex h-screen items-center justify-center bg-[var(--bg-primary)]" role="alert" aria-live="assertive">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold tracking-tight">404</h1>
        <p className="text-sm text-[var(--text-secondary)]">Page not found</p>
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-lg bg-[var(--bg-secondary)] border border-[var(--border)] px-4 py-2 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
          Go home
        </Link>
      </div>
    </div>
  );
}
