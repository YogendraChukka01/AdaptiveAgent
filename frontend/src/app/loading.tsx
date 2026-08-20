export default function Loading() {
  return (
    <div className="flex h-screen items-center justify-center bg-[var(--bg-primary)]" role="status" aria-live="polite">
      <div className="flex items-center gap-3 text-[var(--text-secondary)]">
        <div className="h-4 w-4 animate-spin rounded-full border-2 border-[var(--text-tertiary)] border-t-[var(--accent)]" />
        <span className="text-sm">Loading...</span>
      </div>
    </div>
  );
}
