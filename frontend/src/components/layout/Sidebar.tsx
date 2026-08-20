"use client";

import { useCallback, useEffect, useState } from "react";
import type { Conversation } from "@/lib/store";
import {
  getConversations,
  deleteConversation,
  renameConversation,
} from "@/lib/store";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
}

export function Sidebar({ open, onClose, activeId, onSelect, onNew }: SidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [isMobile, setIsMobile] = useState(false);

  useEffect(() => {
    const check = () => setIsMobile(window.innerWidth < 768);
    check();
    window.addEventListener("resize", check);
    return () => window.removeEventListener("resize", check);
  }, []);

  useEffect(() => {
    setConversations(getConversations());
  }, [open, activeId]);

  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        if (open) onClose();
        else onClose(); // toggled from header
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [open, onClose]);

  const handleDelete = useCallback(
    (id: string, e: React.MouseEvent) => {
      e.stopPropagation();
      deleteConversation(id);
      setConversations(getConversations());
      if (id === activeId) onNew();
    },
    [activeId, onNew],
  );

  const handleRenameStart = useCallback(
    (id: string, title: string, e: React.MouseEvent) => {
      e.stopPropagation();
      setEditingId(id);
      setEditValue(title);
    },
    [],
  );

  const handleRenameSave = useCallback(
    (id: string) => {
      if (editValue.trim()) {
        renameConversation(id, editValue.trim());
      }
      setEditingId(null);
      setConversations(getConversations());
    },
    [editValue],
  );

  const sidebarContent = (
    <div className="flex h-full flex-col bg-[var(--bg-secondary)]">
      {/* Brand */}
      <div className="flex items-center gap-2.5 px-4 py-4 border-b border-[var(--border)]">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--accent)]">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <span className="text-sm font-semibold">SafeAgent</span>
        {isMobile && (
          <button onClick={onClose} className="ml-auto text-[var(--text-secondary)] hover:text-[var(--text-primary)]" aria-label="Close sidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M18 6 6 18M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* New Chat */}
      <div className="px-3 pt-3 pb-1">
        <button
          onClick={onNew}
          className="flex w-full items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] px-3 py-2 text-xs font-medium text-[var(--text-primary)] hover:bg-[var(--bg-hover)] transition-colors"
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M12 5v14M5 12h14" />
          </svg>
          New chat
        </button>
      </div>

      {/* Conversations */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
        <div className="text-[11px] font-medium uppercase tracking-wider text-[var(--text-tertiary)] px-1 mb-2">
          Recent
        </div>
        <div className="space-y-0.5">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => {
                onSelect(conv.id);
                if (isMobile) onClose();
              }}
              className={`group flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs cursor-pointer transition-colors ${
                conv.id === activeId
                  ? "bg-[var(--accent-subtle)] text-[var(--text-primary)]"
                  : "text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
              }`}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="shrink-0 text-[var(--text-tertiary)]">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              {editingId === conv.id ? (
                <input
                  autoFocus
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={() => handleRenameSave(conv.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameSave(conv.id);
                    if (e.key === "Escape") setEditingId(null);
                  }}
                  className="flex-1 bg-transparent border-b border-[var(--accent)] outline-none text-xs"
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="flex-1 truncate">{conv.title}</span>
              )}
              <div className="hidden group-hover:flex items-center gap-1 shrink-0">
                <button
                  onClick={(e) => handleRenameStart(conv.id, conv.title, e)}
                  className="text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                  aria-label="Rename"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z" />
                  </svg>
                </button>
                <button
                  onClick={(e) => handleDelete(conv.id, e)}
                  className="text-[var(--text-tertiary)] hover:text-[var(--danger)]"
                  aria-label="Delete"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M3 6h18M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <div className="border-t border-[var(--border)] px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--bg-tertiary)] text-[11px] font-medium text-[var(--text-secondary)]">
            U
          </div>
          <span className="text-xs text-[var(--text-secondary)] truncate">User</span>
        </div>
      </div>
    </div>
  );

  // Mobile: drawer with backdrop
  if (isMobile) {
    if (!open) return null;
    return (
      <div className="fixed inset-0 z-40">
        <div className="absolute inset-0 bg-black/50" onClick={onClose} />
        <div className="absolute inset-y-0 left-0 w-72 animate-in slide-in-from-left duration-200">
          {sidebarContent}
        </div>
      </div>
    );
  }

  // Desktop: collapsible sidebar
  return (
    <div
      className={`flex-shrink-0 border-r border-[var(--border)] transition-all duration-200 overflow-hidden ${
        open ? "w-64" : "w-0"
      }`}
    >
      <div className="w-64">{sidebarContent}</div>
    </div>
  );
}
