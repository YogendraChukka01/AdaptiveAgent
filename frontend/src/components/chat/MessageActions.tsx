"use client";

import { useCallback, useState } from "react";

interface MessageActionsProps {
  content: string;
  isUser: boolean;
  onRegenerate?: () => void;
}

export function MessageActions({ content, isUser, onRegenerate }: MessageActionsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(() => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }, [content]);

  if (!content) return null;

  return (
    <div className="mt-1.5 flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
      <button
        onClick={handleCopy}
        aria-label={copied ? "Copied" : "Copy message"}
        className="flex h-7 items-center gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
      >
        {copied ? (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M20 6 9 17l-5-5" />
          </svg>
        ) : (
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <rect width="14" height="14" x="8" y="8" rx="2" ry="2" />
            <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2" />
          </svg>
        )}
        {copied ? "Copied" : "Copy"}
      </button>
      {!isUser && onRegenerate && (
        <button
          onClick={onRegenerate}
          aria-label="Regenerate response"
          className="flex h-7 items-center gap-1 rounded-md px-2 text-[11px] text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 12a9 9 0 0 0-9-9 9.75 9.75 0 0 0-6.74 2.74L3 8" />
            <path d="M3 3v5h5" />
            <path d="M3 12a9 9 0 0 0 9 9 9.75 9.75 0 0 0 6.74-2.74L21 16" />
            <path d="M21 21v-5h-5" />
          </svg>
          Retry
        </button>
      )}
    </div>
  );
}
