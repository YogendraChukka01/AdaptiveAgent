"use client";

import React from "react";
import type { ChatMessage } from "@/lib/api";
import { CodeBlock } from "./CodeBlock";
import { MessageActions } from "./MessageActions";

interface MessageBubbleProps {
  message: ChatMessage;
  onRegenerate?: () => void;
}

function parseInlineMarkdown(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = [];
  const regex = /(`[^`]+`)|(\*\*[^*]+\*\*)|(\*[^*]+\*)|(\[[^\]]+\]\([^)]+\))/g;
  let lastIndex = 0;
  let match;
  let key = 0;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      parts.push(text.slice(lastIndex, match.index));
    }
    if (match[1]) {
      parts.push(
        <code key={key++} className="rounded bg-[var(--bg-tertiary)] px-1.5 py-0.5 text-[13px]">
          {match[1].slice(1, -1)}
        </code>,
      );
    } else if (match[2]) {
      parts.push(<strong key={key++}>{match[2].slice(2, -2)}</strong>);
    } else if (match[3]) {
      parts.push(<em key={key++}>{match[3].slice(1, -1)}</em>);
    } else if (match[4]) {
      const m = match[4].match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (m) {
        parts.push(
          <a key={key++} href={m[2]} target="_blank" rel="noopener noreferrer" className="text-[var(--accent)] hover:underline">
            {m[1]}
          </a>,
        );
      }
    }
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) parts.push(text.slice(lastIndex));
  return parts;
}

function renderMarkdown(content: string): React.ReactNode {
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let i = 0;
  let key = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      i++; // skip closing ```
      elements.push(<CodeBlock key={key++} language={lang} code={codeLines.join("\n")} />);
      continue;
    }

    // Heading
    const headingMatch = line.match(/^(#{1,6})\s+(.+)/);
    if (headingMatch) {
      const level = headingMatch[1].length;
      const sizes = ["text-base", "text-base", "text-sm", "text-sm", "text-xs", "text-xs"];
      elements.push(
        <div key={key++} className={`${sizes[level - 1]} font-semibold mt-3 mb-1`}>
          {parseInlineMarkdown(headingMatch[2])}
        </div>,
      );
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith("> ")) {
      elements.push(
        <blockquote key={key++} className="border-l-2 border-[var(--accent)] pl-3 my-2 text-[var(--text-secondary)]">
          {parseInlineMarkdown(line.slice(2))}
        </blockquote>,
      );
      i++;
      continue;
    }

    // Unordered list
    if (line.match(/^[\s]*[-*]\s+/)) {
      const listItems: React.ReactNode[] = [];
      while (i < lines.length && lines[i].match(/^[\s]*[-*]\s+/)) {
        const text = lines[i].replace(/^[\s]*[-*]\s+/, "");
        listItems.push(
          <li key={key++}>{parseInlineMarkdown(text)}</li>,
        );
        i++;
      }
      elements.push(
        <ul key={key++} className="list-disc list-inside my-1 space-y-0.5 text-[13px]">
          {listItems}
        </ul>,
      );
      continue;
    }

    // Ordered list
    if (line.match(/^\d+\.\s+/)) {
      const listItems: React.ReactNode[] = [];
      while (i < lines.length && lines[i].match(/^\d+\.\s+/)) {
        const text = lines[i].replace(/^\d+\.\s+/, "");
        listItems.push(
          <li key={key++}>{parseInlineMarkdown(text)}</li>,
        );
        i++;
      }
      elements.push(
        <ol key={key++} className="list-decimal list-inside my-1 space-y-0.5 text-[13px]">
          {listItems}
        </ol>,
      );
      continue;
    }

    // Horizontal rule
    if (line.match(/^[-*_]{3,}$/)) {
      elements.push(<hr key={key++} className="my-3 border-[var(--border)]" />);
      i++;
      continue;
    }

    // Empty line
    if (line.trim() === "") {
      i++;
      continue;
    }

    // Regular paragraph
    const paraLines: string[] = [];
    while (i < lines.length && lines[i].trim() !== "" && !lines[i].startsWith("```") && !lines[i].match(/^#{1,6}\s/) && !lines[i].startsWith("> ") && !lines[i].match(/^[\s]*[-*]\s+/) && !lines[i].match(/^\d+\.\s+/)) {
      paraLines.push(lines[i]);
      i++;
    }
    if (paraLines.length > 0) {
      elements.push(
        <p key={key++} className="text-[13px] leading-relaxed whitespace-pre-wrap">
          {parseInlineMarkdown(paraLines.join("\n"))}
        </p>,
      );
    }
  }

  return elements;
}

export const MessageBubble = React.memo(function MessageBubble({ message, onRegenerate }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isEmpty = !message.content;

  return (
    <div className={`group flex ${isUser ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-[85%] lg:max-w-[70%] ${isUser ? "" : ""}`}>
        {/* Avatar + content */}
        <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
          {!isUser && (
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--bg-tertiary)] mt-0.5">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="text-[var(--text-secondary)]">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
          )}

          <div className="flex-1 min-w-0">
            {isEmpty ? (
              <div className="flex items-center gap-1.5 py-3">
                <div className="h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-pulse" />
                <div className="h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-pulse [animation-delay:150ms]" />
                <div className="h-1.5 w-1.5 rounded-full bg-[var(--text-tertiary)] animate-pulse [animation-delay:300ms]" />
              </div>
            ) : isUser ? (
              <div className="rounded-xl bg-[var(--accent)] text-white px-4 py-2.5 text-[13px] leading-relaxed whitespace-pre-wrap">
                {message.content}
              </div>
            ) : (
              <div className="text-[var(--text-primary)]">
                {renderMarkdown(message.content)}
              </div>
            )}

            {!isUser && !isEmpty && (
              <MessageActions
                content={message.content}
                isUser={false}
                onRegenerate={onRegenerate}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
});
