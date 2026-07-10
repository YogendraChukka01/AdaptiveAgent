import { useEffect, useRef, useState } from "react";
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
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const handle = async (action: "approve" | "reject") => {
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
  };

  return (
    <div className="rounded-xl border border-amber-500/40 bg-amber-500/5 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <span className="text-amber-400">⚠️</span>
        <span className="font-medium text-amber-200">Action requires your approval</span>
      </div>
      <div className="text-sm text-[var(--text-secondary)] space-y-1">
        <p>
          Risk level:{" "}
          <span className="font-mono text-[var(--text-primary)]">
            {payload.risk_level ?? "unknown"}
          </span>{" "}
          (score {payload.risk_score ?? "?"}) — status:{" "}
          {payload.approval_status ?? "pending"}
        </p>
        {payload.reason && <p>{payload.reason}</p>}
        {payload.pending_tools && payload.pending_tools.length > 0 && (
          <p>
            Tools awaiting review:{" "}
            {payload.pending_tools.map((t) => (
              <code key={t} className="mr-1 rounded bg-black/30 px-1">
                {t}
              </code>
            ))}
          </p>
        )}
        <p className="text-xs opacity-70">
          This request was paused before executing any tools. Approve only if you trust the action.
        </p>
      </div>
      {error && <p className="text-sm text-red-400">{error}</p>}
      <div className="flex gap-2">
        <button
          onClick={() => handle("approve")}
          disabled={pending}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          onClick={() => handle("reject")}
          disabled={pending}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-500 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
