"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Application error:", error);
  }, [error]);

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--bg-primary)]" role="alert" aria-live="assertive">
      <div className="text-center space-y-4 max-w-md">
        <div className="flex justify-center">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[var(--danger)]/10">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--danger)]">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v4M12 16h.01" />
            </svg>
          </div>
        </div>
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          Something went wrong
        </h2>
        <p className="text-xs text-[var(--text-secondary)]">
          {process.env.NODE_ENV === "production"
            ? error.digest || "An unexpected error occurred."
            : error.digest || error.message || "An unexpected error occurred."}
        </p>
        <button
          onClick={reset}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-xs font-medium text-white hover:bg-[var(--accent-hover)] transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
