"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  streamChat,
  uploadDocument,
  type ApprovalPayload,
  type ChatResult,
} from "@/lib/api";
import {
  saveConversation,
  getConversation,
  createConversation,
} from "@/lib/store";
import { getSettings, type AppSettings } from "@/lib/settings";
import { initTheme, setTheme, watchSystemTheme } from "@/lib/theme";
import { showToast } from "@/components/ui/Toast";
import { ToastProvider } from "@/components/ui/Toast";
import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ApprovalCard } from "@/components/chat/ApprovalCard";
import { SidePanel } from "@/components/dashboard/SidePanel";
import { SettingsModal } from "@/components/settings/SettingsModal";

const generateId = (): string => {
  try {
    return crypto.randomUUID();
  } catch {
    const arr = new Uint8Array(16);
    crypto.getRandomValues(arr);
    return Array.from(arr, (b) => b.toString(16).padStart(2, "0")).join("");
  }
};

function AppContent() {
  const [settings, setSettings] = useState<AppSettings>(getSettings);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [threadId, setThreadId] = useState(generateId);
  const [lastResult, setLastResult] = useState<ChatResult | null>(null);
  const lastResultRef = useRef<ChatResult | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [approval, setApproval] = useState<ApprovalPayload | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Sync messages ref
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Cleanup abort on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // Theme init
  useEffect(() => {
    initTheme();
    const stopWatching = watchSystemTheme((resolved) => {
      const s = getSettings();
      if (s.theme === "system") {
        document.documentElement.classList.remove("light", "dark");
        document.documentElement.classList.add(resolved);
      }
    });
    return () => stopWatching();
  }, []);

  // Re-apply theme when settings change
  useEffect(() => {
    setTheme(settings.theme);
  }, [settings.theme]);

  // Load sidebar state from localStorage
  useEffect(() => {
    try {
      const stored = localStorage.getItem("adaptiveagent_sidebar_open");
      if (stored !== null) setSidebarOpen(stored === "true");
    } catch {}
  }, []);

  const persistSidebar = useCallback((open: boolean) => {
    setSidebarOpen(open);
    try {
      localStorage.setItem("adaptiveagent_sidebar_open", String(open));
    } catch {}
  }, []);

  // Keyboard shortcut: Ctrl/Cmd+B for sidebar
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "b") {
        e.preventDefault();
        setSidebarOpen((prev) => {
          const next = !prev;
          try {
            localStorage.setItem("adaptiveagent_sidebar_open", String(next));
          } catch {}
          return next;
        });
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Conversation persistence
  const persistMessages = useCallback(
    (msgs: ChatMessage[]) => {
      if (!activeConversationId) return;
      const conv = getConversation(activeConversationId);
      if (conv) {
        conv.messages = msgs;
        conv.updatedAt = Date.now();
        saveConversation(conv);
      }
    },
    [activeConversationId],
  );

  const handleNewConversation = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setLastResult(null);
    setApproval(null);
    setIsLoading(false);
    setIsStreaming(false);
    setActiveConversationId(null);
    setThreadId(generateId());
  }, []);

  const handleSelectConversation = useCallback((id: string) => {
    abortRef.current?.abort();
    const conv = getConversation(id);
    if (conv) {
      setMessages(conv.messages);
      setActiveConversationId(id);
      setThreadId(conv.id);
      setLastResult(null);
      setApproval(null);
      setIsLoading(false);
      setIsStreaming(false);
    }
  }, []);

  const handleSettingsChanged = useCallback((s: AppSettings) => {
    setSettings(s);
  }, []);

  const applyResult = useCallback(
    (result: ChatResult) => {
      lastResultRef.current = result;
      setLastResult(result);
      setMessages((prev) => {
        const updated = [...prev];
        const lastIdx = updated.length - 1;
        if (lastIdx >= 0 && updated[lastIdx].role === "assistant") {
          updated[lastIdx] = {
            ...updated[lastIdx],
            content: result.response || "(no response)",
          };
        }
        persistMessages(updated);
        return updated;
      });
    },
    [persistMessages],
  );

  const handleSend = useCallback(
    async (content: string) => {
      lastResultRef.current = null;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const userMsg: ChatMessage = { id: generateId(), role: "user", content };
      const assistantMsg: ChatMessage = { id: generateId(), role: "assistant", content: "" };

      // Create conversation if new
      let activeId = activeConversationId;
      if (!activeId) {
        const conv = createConversation(threadId, content);
        setActiveConversationId(conv.id);
        activeId = conv.id;
      }

      const newMessages = [...messagesRef.current, userMsg, assistantMsg];
      setMessages(newMessages);
      setIsLoading(true);
      setIsStreaming(true);
      setApproval(null);

      try {
        let fullResponse = "";
        const historyToSend = [...messagesRef.current, userMsg];
        const gen = streamChat(historyToSend, threadId, controller.signal);

        for await (const ev of gen) {
          if (controller.signal.aborted) break;
          if (ev.type === "token") {
            fullResponse += ev.token;
            setMessages((prev) => {
              const updated = [...prev];
              const lastIdx = updated.length - 1;
              if (lastIdx >= 0) {
                updated[lastIdx] = {
                  ...updated[lastIdx],
                  content: fullResponse,
                };
              }
              return updated;
            });
          } else if (ev.type === "complete") {
            applyResult(ev.result);
          } else if (ev.type === "needs_approval") {
            setApproval(ev.payload);
          }
        }

        if (fullResponse && !lastResultRef.current) {
          applyResult({
            response: fullResponse,
            citations: [],
            confidence_score: 0,
            risk_level: "low",
            risk_score: 0,
            reasoning_path: [],
            step_count: 0,
          } as ChatResult);
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        console.error("Stream error:", err);
        setMessages((prev) => {
          const updated = [...prev];
          const lastIdx = updated.length - 1;
          if (lastIdx >= 0) {
            updated[lastIdx] = {
              ...updated[lastIdx],
              content:
                err instanceof Error
                  ? `Error: ${err.message.slice(0, 200)}`
                  : "An unexpected error occurred.",
            };
          }
          return updated;
        });
        showToast("error", "Failed to get response");
      } finally {
        setIsLoading(false);
        setIsStreaming(false);
        // Persist final state
        setMessages((prev) => {
          persistMessages(prev);
          return prev;
        });
      }
    },
    [threadId, activeConversationId, applyResult, persistMessages],
  );

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
    setIsLoading(false);
    setIsStreaming(false);
  }, []);

  const handleUpload = useCallback(
    async (file: File) => {
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;
      setIsLoading(true);
      try {
        const result = await uploadDocument(file, threadId, controller.signal);
        const msg = `Uploaded ${result.filename} (${result.chunks} chunks indexed)`;
        setMessages((prev) => {
          const updated = [
            ...prev,
            { id: generateId(), role: "user" as const, content: `Uploaded: ${result.filename}` },
            { id: generateId(), role: "assistant" as const, content: msg },
          ];
          persistMessages(updated);
          return updated;
        });
        showToast("success", `Uploaded ${result.filename}`);
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return;
        showToast("error", `Upload failed: ${err instanceof Error ? err.message : "Unknown error"}`);
      } finally {
        setIsLoading(false);
      }
    },
    [threadId, persistMessages],
  );

  const handleSuggestion = useCallback(
    (text: string) => {
      handleSend(text);
    },
    [handleSend],
  );

  return (
    <div className="flex h-screen bg-[var(--bg-primary)]">
      {/* Sidebar */}
      <Sidebar
        open={sidebarOpen}
        onClose={() => persistSidebar(false)}
        activeId={activeConversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
      />

      {/* Main area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <Header
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => persistSidebar(!sidebarOpen)}
          modelName={settings.modelName}
          onOpenSettings={() => setSettingsOpen(true)}
          isConnected={null}
        />

        {/* Chat area */}
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto" role="log" aria-live={isLoading ? "off" : "polite"} aria-busy={isLoading} aria-label="Chat messages">
          {messages.length === 0 && !isLoading ? (
            <WelcomeScreen onSuggestion={handleSuggestion} />
          ) : (
            <div className="max-w-3xl mx-auto px-4 py-6">
              {messages.map((msg) => (
                <MessageBubble
                  key={msg.id}
                  message={msg}
                  onRegenerate={
                    msg.role === "assistant" && !isLoading
                      ? () => {
                          // Remove last assistant message and resend
                          setMessages((prev) => prev.slice(0, -1));
                          const lastUser = [...messagesRef.current]
                            .reverse()
                            .find((m) => m.role === "user");
                          if (lastUser) handleSend(lastUser.content);
                        }
                      : undefined
                  }
                />
              ))}
              {approval && (
                <ApprovalCard
                  payload={approval}
                  onResolved={(result) => {
                    setApproval(null);
                    applyResult(result);
                  }}
                />
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Composer */}
        <ChatInput
          onSend={handleSend}
          onUpload={handleUpload}
          onStop={handleStop}
          disabled={isLoading && !isStreaming}
          isStreaming={isStreaming}
        />
      </div>

      {/* Side panel */}
      {showPanel && lastResult && (
        <SidePanel result={lastResult} onClose={() => setShowPanel(false)} />
      )}

      {/* Settings modal */}
      <SettingsModal
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        onSettingsChanged={handleSettingsChanged}
      />
    </div>
  );
}

export default function Home() {
  return (
    <ToastProvider>
      <AppContent />
    </ToastProvider>
  );
}
