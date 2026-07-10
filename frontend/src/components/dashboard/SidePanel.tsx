interface Props {
  result: {
    response?: string;
    confidence_score?: number;
    risk_score?: number;
    risk_level?: string;
    reasoning_path?: string[];
    eval_score?: number;
    eval_details?: string;
    citations?: Array<{
      source: string;
      chunk: string;
      relevance_score: number;
    }>;
    step_count?: number;
  };
  onClose: () => void;
}

function ScoreBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.min(100, Math.max(0, value));
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-[var(--text-secondary)]">
        <span>{label}</span>
        <span>{pct.toFixed(1)}%</span>
      </div>
      <div className="h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function SidePanel({ result, onClose }: Props) {
  const riskColor =
    result.risk_level === "high"
      ? "var(--danger)"
      : result.risk_level === "medium"
        ? "var(--warning)"
        : "var(--success)";

  return (
    <div className="w-96 border-l border-[var(--border)] bg-[var(--bg-secondary)] overflow-y-auto">
      <div className="flex items-center justify-between p-4 border-b border-[var(--border)]">
        <h2 className="text-sm font-semibold">Details</h2>
        <button
          onClick={onClose}
          aria-label="Close details panel"
          className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
        >
          ✕
        </button>
      </div>

      <div className="p-4 space-y-5">
        <div className="space-y-3">
          <h3 className="text-xs font-medium uppercase tracking-wider text-[var(--text-secondary)]">
            Scores
          </h3>
          <ScoreBar
            label="Confidence"
            value={result.confidence_score ?? 0}
            color="var(--accent)"
          />
          <ScoreBar
            label="Risk"
            value={result.risk_score ?? 0}
            color={riskColor}
          />
          {result.eval_score !== undefined && (
            <ScoreBar
              label="Eval"
              value={(result.eval_score ?? 0) * 100}
              color="var(--accent)"
            />
          )}
        </div>

        {result.reasoning_path && result.reasoning_path.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-medium uppercase tracking-wider text-[var(--text-secondary)]">
              Reasoning
            </h3>
            <ol className="space-y-1.5">
              {result.reasoning_path.map((step, i) => (
                <li key={i} className="text-xs text-[var(--text-primary)] flex gap-2">
                  <span className="text-[var(--text-secondary)] shrink-0">{i + 1}.</span>
                  <span>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        )}

        {result.citations && result.citations.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-xs font-medium uppercase tracking-wider text-[var(--text-secondary)]">
              Sources
            </h3>
            <div className="space-y-2">
              {result.citations.map((cite, i) => (
                <div
                  key={i}
                  className="text-xs bg-[var(--bg-tertiary)] rounded-lg p-2.5 space-y-1"
                >
                  <div className="flex justify-between">
                    <span className="text-[var(--text-secondary)] truncate">
                      {cite.source}
                    </span>
                    <span className="text-[var(--accent)]">
                      {(cite.relevance_score ?? 0).toFixed(2)}
                    </span>
                  </div>
                  <p className="text-[var(--text-primary)] line-clamp-2">
                    {cite.chunk}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {result.step_count !== undefined && (
          <div className="text-xs text-[var(--text-secondary)]">
            Steps: {result.step_count}
          </div>
        )}
      </div>
    </div>
  );
}
