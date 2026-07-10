"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ChatMessage,
  streamChat,
  uploadDocument,
  type ApprovalPayload,
  type ChatResult,
} from "@/lib/api";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { ApprovalCard } from "@/components/chat/ApprovalCard";
import { SidePanel } from "@/components/dashboard/SidePanel";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() => crypto.randomUUID());
  const [lastResult, setLastResult] = useState<ChatResult | null>(null);
  const [showPanel, setShowPanel] = useState(false);
  const [approval, setApproval] = useState<ApprovalPayload | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  const applyResult = useCallback((result: ChatResult) => {
    setLastResult(result);
    setMessages((prev) => {
      if (prev.length === 0) return prev;
      const updated = [...prev];
      updated[updated.length - 1] = {
        ...updated[updated.length - 1],
        role: "assistant",
        content: result.response || "(no response)",
      };
      return updated;
    });
  }, []);

  const handleSend = useCallback(async (content: string) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userMsg: ChatMessage = { id: crypto.randomUUID(), role: "user", content };
    const assistantMsg: ChatMessage = { id: crypto.randomUUID(), role: "assistant", content: "" };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsLoading(true);
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
            updated[updated.length - 1] = {
              ...updated[updated.length - 1],
              role: "assistant",
              content: fullResponse,
            };
            return updated;
          });
        } else if (ev.type === "complete") {
          applyResult(ev.result);
        } else if (ev.type === "needs_approval") {
          setApproval(ev.payload);
        }
      }
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          role: "assistant",
          content: "Sorry, an error occurred while processing your request.",
        };
        return updated;
      });
    } finally {
      if (!controller.signal.aborted) setIsLoading(false);
    }
  }, [threadId, applyResult]);

  const handleUpload = useCallback(async (file: File) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    setIsLoading(true);
    try {
      const result = await uploadDocument(file, threadId, controller.signal);
      const msg = `📄 Uploaded **${result.filename}** (${result.chunks} chunks indexed)`;
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: "user", content: `Uploaded: ${result.filename}` },
        { id: crypto.randomUUID(), role: "assistant", content: msg },
      ]);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: "assistant",
          content: `Upload failed: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ]);
    } finally {
      if (!controller.signal.aborted) setIsLoading(false);
    }
  }, [threadId]);

  return (
    <div className="flex h-screen">
      <div className="flex-1 flex flex-col">
        <header className="border-b border-[var(--border)] px-6 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold">SafeAgent</h1>
          <button
            onClick={() => setShowPanel(!showPanel)}
            className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
          >
            {showPanel ? "Hide Details" : "Show Details"}
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {messages.length === 0 && (
            <div className="flex items-center justify-center h-full text-[var(--text-secondary)]">
              <div className="text-center space-y-2">
                <p className="text-xl">Ask me anything</p>
                <p className="text-sm">
                  Upload a document or ask a question to get started
                </p>
              </div>
            </div>
          )}
          {messages.map((msg) => (
            <MessageBubble key={msg.id} message={msg} />
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

        <ChatInput
          onSend={handleSend}
          onUpload={handleUpload}
          disabled={isLoading}
        />
      </div>

      {showPanel && lastResult && (
        <SidePanel result={lastResult} onClose={() => setShowPanel(false)} />
      )}
    </div>
  );
}
