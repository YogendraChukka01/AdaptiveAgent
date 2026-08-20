"use client";

import { useCallback, useEffect, useState } from "react";

interface ToastItem {
  id: number;
  type: "success" | "error" | "info";
  message: string;
}

let toastId = 0;
let listeners: Array<(items: ToastItem[]) => void> = [];
let items: ToastItem[] = [];

function notifyListeners() {
  for (const l of listeners) l([...items]);
}

export function showToast(type: ToastItem["type"], message: string, duration = 4000) {
  const id = ++toastId;
  items = [...items, { id, type, message }];
  notifyListeners();
  setTimeout(() => {
    items = items.filter((t) => t.id !== id);
    notifyListeners();
  }, duration);
}

function ToastContainer() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    listeners.push(setToasts);
    return () => {
      listeners = listeners.filter((l) => l !== setToasts);
    };
  }, []);

  const dismiss = useCallback((id: number) => {
    items = items.filter((t) => t.id !== id);
    notifyListeners();
  }, []);

  if (toasts.length === 0) return null;

  const icons: Record<string, string> = {
    success: "M20 6 9 17l-5-5",
    error: "M18 6 6 18M6 6l12 12",
    info: "M12 16v-4M12 8h.01",
  };

  const colors: Record<string, string> = {
    success: "text-[var(--success)]",
    error: "text-[var(--danger)]",
    info: "text-[var(--accent)]",
  };

  return (
    <div className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2" role="status" aria-live="polite">
      {toasts.map((t) => (
        <div
          key={t.id}
          className="flex items-center gap-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3.5 py-2.5 shadow-lg animate-in fade-in slide-in-from-bottom-2"
          role="alert"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={colors[t.type]}>
            <circle cx="12" cy="12" r="10" className="opacity-20" />
            <path d={icons[t.type]} />
          </svg>
          <span className="text-xs text-[var(--text-primary)]">{t.message}</span>
          <button
            onClick={() => dismiss(t.id)}
            aria-label="Dismiss"
            className="ml-2 text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
          >
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  return (
    <>
      {children}
      <ToastContainer />
    </>
  );
}
