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
    <div className="flex h-screen items-center justify-center bg-[var(--bg-primary)]">
      <div className="text-center space-y-4 max-w-md">
        <h2 className="text-lg font-semibold text-[var(--text-primary)]">
          Something went wrong
        </h2>
        <p className="text-sm text-[var(--text-secondary)]">
          {error.digest || error.message || "An unexpected error occurred."}
        </p>
        <button
          onClick={reset}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-white hover:bg-[var(--accent-hover)] transition-colors"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
