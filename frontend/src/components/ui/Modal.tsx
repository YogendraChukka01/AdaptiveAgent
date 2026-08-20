"use client";

import { useCallback, useEffect, useRef } from "react";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
  width?: string;
}

export function Modal({ open, onClose, title, children, width = "max-w-lg" }: ModalProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const el = dialogRef.current;
    if (!el) return;
    if (open && !el.open) {
      el.showModal();
    } else if (!open && el.open) {
      el.close();
    }
  }, [open]);

  const handleCancel = useCallback(
    (e: React.SyntheticEvent<HTMLDialogElement>) => {
      e.preventDefault();
      onClose();
    },
    [onClose],
  );

  const handleBackdropClick = useCallback(
    (e: React.MouseEvent<HTMLDialogElement>) => {
      if (e.target === e.currentTarget) onClose();
    },
    [onClose],
  );

  return (
    <dialog
      ref={dialogRef}
      onCancel={handleCancel}
      onClick={handleBackdropClick}
      className={`fixed inset-0 z-50 m-auto ${width} rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] p-0 shadow-lg backdrop:bg-black/50 backdrop:backdrop-blur-sm`}
    >
      <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-3.5">
        <h2 className="text-sm font-semibold">{title}</h2>
        <button
          onClick={onClose}
          aria-label="Close"
          className="flex h-7 w-7 items-center justify-center rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)]"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18 6 6 18" /><path d="m6 6 12 12" />
          </svg>
        </button>
      </div>
      <div className="max-h-[70vh] overflow-y-auto p-5">{children}</div>
    </dialog>
  );
}
