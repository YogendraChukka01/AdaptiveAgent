"use client";

import { useEffect, useRef, useState } from "react";
import type { ChatResult } from "@/lib/api";

interface Props {
  result: Partial<ChatResult>;
  onClose: () => void;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px] text-[var(--text-secondary)]">
        <span>{label}</span>
        <span>{pct.toFixed(1)}%</span>
      </div>
      <div
        role="progressbar"
        aria-valuenow={pct}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${label}: ${pct.toFixed(1)}%`}
        className="h-1.5 bg-[var(--bg-tertiary)] rounded-full overflow-hidden"
      >
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function SidePanel({ result, onClose }: Props) {
  const panelRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    panelRef.current?.focus();
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") onCloseRef.current();
    };
    document.addEventListener("keydown", handleEscape);
    return () => document.removeEventListener("keydown", handleEscape);
  }, []);

  const riskColor =
    result.risk_level === "high"
      ? "var(--danger)"
      : result.risk_level === "medium"
        ? "var(--warning)"
        : "var(--success)";

  const panel = (
    <div
      ref={panelRef}
      tabIndex={-1}
      role="complementary"
      aria-label="Response details"
      className="h-full bg-[var(--bg-secondary)] overflow-y-auto outline-none"
    >
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <h2 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-secondary)]">Details</h2>
        <button
          onClick={onClose}
          aria-label="Close details panel"
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>
      </div>

      <div className="p-4 space-y-5">
        {/* Scores */}
        <div className="space-y-3">
          <ScoreBar label="Confidence" value={result.confidence_score ?? 0} color="var(--accent)" />
          <ScoreBar label="Risk" value={result.risk_score ?? 0} color={riskColor} />
          {result.eval_score !== undefined && (
            <ScoreBar label="Eval" value={(result.eval_score ?? 0) * 100} color="var(--accent)" />
          )}
        </div>

        {/* Reasoning */}
        {result.reasoning_path && result.reasoning_path.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-tertiary)]">Reasoning</h3>
            <ol className="space-y-1.5">
              {result.reasoning_path.map((step, i) => (
                <li key={`step-${i}`} className="text-[11px] text-[var(--text-secondary)] flex gap-2">
                  <span className="text-[var(--text-tertiary)] shrink-0">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {/* Citations */}
        {result.citations && result.citations.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-tertiary)]">Sources</h3>
            <div className="space-y-2">
              {result.citations.map((cite, i) => (
                <div
                  key={`cite-${i}`}
                  className="text-[11px] bg-[var(--bg-tertiary)] rounded-lg p-2.5 space-y-1"
                >
                  <div className="flex justify-between">
                    <span className="text-[var(--text-secondary)] truncate">{cite.source}</span>
                    <span className="text-[var(--accent)] shrink-0">{(cite.relevance_score ?? 0).toFixed(2)}</span>
                  </div>
                  <p className="text-[var(--text-primary)] line-clamp-2">{cite.chunk}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step count */}
        {result.step_count !== undefined && (
          <div className="text-[11px] text-[var(--text-tertiary)]">
            Steps: {result.step_count}
          </div>
        )}
      </div>
    </div>
  );

  // Mobile: slide-over overlay
  if (isMobile) {
    return (
      <div className="fixed inset-0 z-40">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        <div className="absolute inset-y-0 right-0 w-full max-w-sm animate-in slide-in-from-right duration-200">
          {panel}
        </div>
      </div>
    );
  }

  // Desktop: sidebar panel
  return (
    <div className="w-80 border-l border-[var(--border)] flex-shrink-0">
      {panel}
    </div>
  );
}
