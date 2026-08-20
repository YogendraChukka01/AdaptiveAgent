"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  approveAction,
  type ApprovalPayload,
  type ChatResult,
} from "@/lib/api";

interface Props {
  payload: ApprovalPayload;
  onResolved: (result: ChatResult) => void;
}

export function ApprovalCard({ payload, onResolved }: Props) {
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handle = useCallback(async (action: "approve" | "reject") => {
    if (action === "approve" && !confirming) {
      setConfirming(true);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setPending(true);
    setError(null);
    try {
      const result = await approveAction(payload.thread_id, action, controller.signal);
      setPending(false);
      onResolved(result);
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      setError(e instanceof Error ? e.message : "Approval failed");
      setPending(false);
    }
  }, [payload.thread_id, onResolved, confirming]);

  return (
    <div className="rounded-xl border border-[var(--warning)]/30 bg-[var(--accent-subtle)] p-4 space-y-3">
      <div className="flex items-center gap-2">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--warning)]">
          <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z" />
          <path d="M12 9v4M12 17h.01" />
        </svg>
        <span className="text-sm font-medium text-[var(--text-primary)]">Action requires approval</span>
      </div>

      <div className="text-xs text-[var(--text-secondary)] space-y-1.5">
        <div className="flex items-center gap-3">
          <span>Risk level:</span>
          <span className="font-mono text-[var(--text-primary)]">{payload.risk_level ?? "unknown"}</span>
          <span>Score: {payload.risk_score ?? "?"}</span>
        </div>
        {payload.reason && <p>{payload.reason}</p>}
        {payload.triggering_factors && payload.triggering_factors.length > 0 && (
          <div>
            <span>Triggering factors: </span>
            {payload.triggering_factors.map((f, i) => (
              <span key={i} className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] mr-1">
                {f}
              </span>
            ))}
          </div>
        )}
        {payload.pending_tools && payload.pending_tools.length > 0 && (
          <div>
            <span>Tools: </span>
            {payload.pending_tools.map((t, i) => (
              <code key={`${t}-${i}`} className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[10px] mr-1">
                {t}
              </code>
            ))}
          </div>
        )}
      </div>

      {error && (
        <p role="alert" className="text-xs text-[var(--danger)]">{error}</p>
      )}

      <div className="flex gap-2">
        {confirming ? (
          <>
            <button
              type="button"
              onClick={() => handle("approve")}
              disabled={pending}
              className="rounded-lg bg-[var(--danger)] px-4 py-1.5 text-xs font-medium text-white hover:bg-red-600 disabled:opacity-50 transition-colors"
            >
              {pending ? (
                <span className="flex items-center gap-1.5">
                  <span className="h-3 w-3 animate-spin rounded-full border border-white/30 border-t-white" />
                  Processing
                </span>
              ) : (
                "Confirm approve"
              )}
            </button>
            <button
              type="button"
              onClick={() => setConfirming(false)}
              disabled={pending}
              className="rounded-lg bg-[var(--bg-tertiary)] px-4 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50 transition-colors"
            >
              Cancel
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              onClick={() => handle("approve")}
              disabled={pending}
              className="rounded-lg bg-[var(--success)] px-4 py-1.5 text-xs font-medium text-white hover:bg-green-600 disabled:opacity-50 transition-colors"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => handle("reject")}
              disabled={pending}
              className="rounded-lg bg-[var(--bg-tertiary)] px-4 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50 transition-colors"
            >
              Reject
            </button>
          </>
        )}
      </div>
    </div>
  );
}
