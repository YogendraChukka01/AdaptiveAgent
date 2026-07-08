"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ChatMessage, streamChat, sendMessage, uploadDocument } from "@/lib/api";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { ChatInput } from "@/components/chat/ChatInput";
import { SidePanel } from "@/components/dashboard/SidePanel";

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [threadId] = useState(() => crypto.randomUUID());
  const [lastResult, setLastResult] = useState<any>(null);
  const [showPanel, setShowPanel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(async (content: string) => {
    const userMsg: ChatMessage = { role: "user", content };
    const updatedMessages = [...messages, userMsg];
    setMessages(updatedMessages);
    setIsLoading(true);
    setLastResult(null);

    if ("ai" !== "ignore") {
      const assistantMsg: ChatMessage = { role: "assistant", content: "" };
      setMessages((prev) => [...prev, assistantMsg]);

      try {
        let fullResponse = "";
        let result: any = null;
        const gen = streamChat(updatedMessages, threadId);
        while (true) {
          const { value, done } = await gen.next();
          if (done) {
            result = value;
            break;
          }
          fullResponse += value;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: fullResponse,
            };
            return updated;
          });
        }

        setLastResult(result);
        if (result?.response) {
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: result.response,
            };
            return updated;
          });
        }
      } catch (err) {
        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: "Sorry, an error occurred while processing your request.",
          };
          return updated;
        });
      }
    }

    setIsLoading(false);
  }, [messages, threadId]);

  const handleUpload = useCallback(async (file: File) => {
    try {
      const result = await uploadDocument(file, threadId);
      const msg = `📄 Uploaded **${result.filename}** (${result.chunks} chunks indexed)`;
      setMessages((prev) => [
        ...prev,
        { role: "user", content: `Uploaded: ${result.filename}` },
        { role: "assistant", content: msg },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Upload failed: ${err instanceof Error ? err.message : "Unknown error"}`,
        },
      ]);
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
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
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
