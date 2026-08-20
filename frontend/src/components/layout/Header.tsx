"use client";

interface HeaderProps {
  sidebarOpen: boolean;
  onToggleSidebar: () => void;
  modelName: string;
  onOpenSettings: () => void;
  isConnected: boolean | null;
}

export function Header({
  sidebarOpen,
  onToggleSidebar,
  modelName,
  onOpenSettings,
  isConnected,
}: HeaderProps) {
  return (
    <header className="flex items-center gap-3 border-b border-[var(--border)] bg-[var(--bg-primary)] px-4 py-2.5">
      {/* Sidebar toggle */}
      <button
        onClick={onToggleSidebar}
        aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
        className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          {sidebarOpen ? (
            <>
              <rect width="18" height="18" x="3" y="3" rx="2" />
              <path d="M9 3v18" />
            </>
          ) : (
            <>
              <path d="M21 12H3M21 6H3M21 18H3" />
            </>
          )}
        </svg>
      </button>

      {/* Center: model indicator */}
      <div className="flex-1 flex items-center justify-center gap-2">
        <div className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)]">
          <div className={`h-1.5 w-1.5 rounded-full ${isConnected === false ? "bg-[var(--danger)]" : isConnected === null ? "bg-[var(--warning)]" : "bg-[var(--success)]"}`} />
          <span className="font-medium">{modelName || "No model configured"}</span>
        </div>
      </div>

      {/* Settings */}
      <button
        onClick={onOpenSettings}
        aria-label="Settings"
        className="flex h-8 w-8 items-center justify-center rounded-md text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-primary)] transition-colors"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </button>
    </header>
  );
}
