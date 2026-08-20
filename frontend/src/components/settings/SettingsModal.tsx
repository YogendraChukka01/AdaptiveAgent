"use client";

import { useCallback, useState } from "react";
import { Modal } from "@/components/ui/Modal";
import { showToast } from "@/components/ui/Toast";
import {
  getSettings,
  updateSettings,
  resetSettings,
  testApiConnection,
  type AppSettings,
} from "@/lib/settings";
import { getConversations } from "@/lib/store";

interface Props {
  open: boolean;
  onClose: () => void;
  onSettingsChanged: (settings: AppSettings) => void;
}

type Tab = "provider" | "appearance" | "data";

export function SettingsModal({ open, onClose, onSettingsChanged }: Props) {
  const [settings, setSettings] = useState<AppSettings>(getSettings);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; error?: string } | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("provider");

  const update = useCallback(
    (partial: Partial<AppSettings>) => {
      const updated = updateSettings(partial);
      setSettings(updated);
      onSettingsChanged(updated);
    },
    [onSettingsChanged],
  );

  const handleTest = useCallback(async () => {
    setTesting(true);
    setTestResult(null);
    const result = await testApiConnection(settings.apiBaseUrl, settings.apiKey);
    setTestResult(result);
    setTesting(false);
    showToast(
      result.ok ? "success" : "error",
      result.ok ? "Connection successful" : `Connection failed: ${result.error}`,
    );
  }, [settings.apiBaseUrl, settings.apiKey]);

  const handleReset = useCallback(() => {
    const defaults = resetSettings();
    setSettings(defaults);
    onSettingsChanged(defaults);
    showToast("info", "Settings reset to defaults");
  }, [onSettingsChanged]);

  const handleExport = useCallback(() => {
    const convs = getConversations();
    const data = JSON.stringify(convs, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `safeagent-export-${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast("success", "Conversations exported");
  }, []);

  const handleClearHistory = useCallback(() => {
    if (confirm("Clear all conversations? This cannot be undone.")) {
      localStorage.removeItem("adaptiveagent_conversations");
      showToast("info", "Conversation history cleared");
    }
  }, []);

  const tabs: { id: Tab; label: string }[] = [
    { id: "provider", label: "Provider" },
    { id: "appearance", label: "Appearance" },
    { id: "data", label: "Data" },
  ];

  return (
    <Modal open={open} onClose={onClose} title="Settings" width="max-w-xl">
      {/* Tabs */}
      <div className="flex gap-1 border-b border-[var(--border)] -mx-5 px-5 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-3 py-2 text-xs font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? "border-[var(--accent)] text-[var(--text-primary)]"
                : "border-transparent text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Provider */}
      {activeTab === "provider" && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              API Base URL
            </label>
            <input
              type="url"
              value={settings.apiBaseUrl}
              onChange={(e) => update({ apiBaseUrl: e.target.value })}
              placeholder="http://localhost:8000"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none focus:border-[var(--accent)]"
            />
            <p className="mt-1 text-[10px] text-[var(--text-tertiary)]">
              Backend endpoint. Leave empty to use the default backend URL.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              API Key
            </label>
            <input
              type="password"
              value={settings.apiKey}
              onChange={(e) => update({ apiKey: e.target.value })}
              placeholder="Optional"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none focus:border-[var(--accent)]"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5">
              Model Name
            </label>
            <input
              type="text"
              value={settings.modelName}
              onChange={(e) => update({ modelName: e.target.value })}
              placeholder="qwen2.5:7b"
              className="w-full rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] px-3 py-2 text-xs text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none focus:border-[var(--accent)]"
            />
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleTest}
              disabled={testing || !settings.apiBaseUrl}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] disabled:opacity-50 transition-colors"
            >
              {testing ? (
                <span className="flex items-center gap-1.5">
                  <span className="h-3 w-3 animate-spin rounded-full border border-[var(--text-tertiary)] border-t-[var(--text-primary)]" />
                  Testing...
                </span>
              ) : (
                "Test Connection"
              )}
            </button>
            {testResult && (
              <span className={`text-xs ${testResult.ok ? "text-[var(--success)]" : "text-[var(--danger)]"}`}>
                {testResult.ok ? "Connected" : testResult.error}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Appearance */}
      {activeTab === "appearance" && (
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-[var(--text-secondary)] mb-2">Theme</label>
            <div className="flex gap-2">
              {(["dark", "light", "system"] as const).map((theme) => (
                <button
                  key={theme}
                  onClick={() => update({ theme })}
                  className={`rounded-lg border px-4 py-2 text-xs font-medium transition-colors ${
                    settings.theme === theme
                      ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--text-primary)]"
                      : "border-[var(--border)] bg-[var(--bg-secondary)] text-[var(--text-secondary)] hover:bg-[var(--bg-hover)]"
                  }`}
                >
                  {theme.charAt(0).toUpperCase() + theme.slice(1)}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div>
              <div className="text-xs font-medium text-[var(--text-secondary)]">Enter to send</div>
              <div className="text-[10px] text-[var(--text-tertiary)]">Press Enter to send, Shift+Enter for new line</div>
            </div>
            <button
              onClick={() => update({ enterToSend: !settings.enterToSend })}
              className={`relative h-5 w-9 rounded-full transition-colors ${settings.enterToSend ? "bg-[var(--accent)]" : "bg-[var(--bg-tertiary)]"}`}
              role="switch"
              aria-checked={settings.enterToSend}
            >
              <span className={`absolute top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${settings.enterToSend ? "left-[18px]" : "left-0.5"}`} />
            </button>
          </div>
        </div>
      )}

      {/* Data */}
      {activeTab === "data" && (
        <div className="space-y-4">
          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] p-3">
            <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">Export conversations</div>
            <div className="text-[10px] text-[var(--text-tertiary)] mb-2">
              Download all conversations as a JSON file.
            </div>
            <button
              onClick={handleExport}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
            >
              Export
            </button>
          </div>

          <div className="rounded-lg border border-[var(--danger)]/30 bg-[var(--bg-primary)] p-3">
            <div className="text-xs font-medium text-[var(--danger)] mb-1">Clear history</div>
            <div className="text-[10px] text-[var(--text-tertiary)] mb-2">
              Delete all conversations from local storage. This cannot be undone.
            </div>
            <button
              onClick={handleClearHistory}
              className="rounded-lg border border-[var(--danger)]/50 px-3 py-1.5 text-xs font-medium text-[var(--danger)] hover:bg-[var(--danger)]/10 transition-colors"
            >
              Clear All
            </button>
          </div>

          <div className="rounded-lg border border-[var(--border)] bg-[var(--bg-primary)] p-3">
            <div className="text-xs font-medium text-[var(--text-secondary)] mb-1">Reset settings</div>
            <div className="text-[10px] text-[var(--text-tertiary)] mb-2">
              Reset all settings to their default values.
            </div>
            <button
              onClick={handleReset}
              className="rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] transition-colors"
            >
              Reset Settings
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
