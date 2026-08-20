"use client";

import { useCallback, useRef, useState } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  onUpload: (file: File) => void;
  onStop?: () => void;
  disabled: boolean;
  isStreaming?: boolean;
}

const ACCEPTED_TYPES = new Set([
  "text/plain",
  "text/markdown",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const MAX_FILE_SIZE = 10 * 1024 * 1024;

interface AttachedFile {
  file: File;
  preview?: string;
}

export function ChatInput({ onSend, onUpload, onStop, disabled, isStreaming }: ChatInputProps) {
  const [input, setInput] = useState("");
  const [fileError, setFileError] = useState<string | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const [showAttach, setShowAttach] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const submitIfReady = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || disabled) return;

    // Upload attached files first
    for (const af of attachedFiles) {
      onUpload(af.file);
    }
    setAttachedFiles([]);

    onSend(trimmed);
    setInput("");
    setFileError(null);

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, disabled, attachedFiles, onSend, onUpload]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      submitIfReady();
    },
    [submitIfReady],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitIfReady();
      }
    },
    [submitIfReady],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      setInput(e.target.value);
      setFileError(null);

      // Auto-resize
      const el = e.target;
      el.style.height = "auto";
      el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
    },
    [],
  );

  const handleFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files) return;

      for (const file of Array.from(files)) {
        if (!ACCEPTED_TYPES.has(file.type) && !file.name.match(/\.(txt|md|pdf|docx)$/i)) {
          setFileError("Unsupported file type. Upload .txt, .md, .pdf, or .docx");
          continue;
        }
        if (file.size > MAX_FILE_SIZE) {
          setFileError("File too large. Maximum size is 10 MB.");
          continue;
        }

        if (file.type.startsWith("image/")) {
          const reader = new FileReader();
          reader.onload = () => {
            setAttachedFiles((prev) => [...prev, { file, preview: reader.result as string }]);
          };
          reader.readAsDataURL(file);
        } else {
          setAttachedFiles((prev) => [...prev, { file }]);
        }
      }

      setShowAttach(false);
      e.target.value = "";
    },
    [],
  );

  const removeFile = useCallback((index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const getFileIcon = (name: string) => {
    if (name.endsWith(".pdf")) return "PDF";
    if (name.endsWith(".docx") || name.endsWith(".doc")) return "DOC";
    if (name.endsWith(".md")) return "MD";
    return "TXT";
  };

  return (
    <form onSubmit={handleSubmit} className="border-t border-[var(--border)] bg-[var(--bg-primary)]">
      {/* File error */}
      {fileError && (
        <div role="alert" className="max-w-3xl mx-auto px-4 pt-3 text-xs text-[var(--danger)]">
          {fileError}
        </div>
      )}

      {/* Attached files preview */}
      {attachedFiles.length > 0 && (
        <div className="max-w-3xl mx-auto px-4 pt-3 flex gap-2 flex-wrap">
          {attachedFiles.map((af, i) => (
            <div
              key={`${af.file.name}-${i}`}
              className="flex items-center gap-2 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-2.5 py-1.5 text-xs animate-in fade-in"
            >
              {af.preview ? (
                <img src={af.preview} alt="" className="h-6 w-6 rounded object-cover" />
              ) : (
                <span className="flex h-6 w-6 items-center justify-center rounded bg-[var(--bg-tertiary)] text-[9px] font-bold text-[var(--text-tertiary)]">
                  {getFileIcon(af.file.name)}
                </span>
              )}
              <span className="text-[var(--text-secondary)] truncate max-w-[120px]">{af.file.name}</span>
              <button
                type="button"
                onClick={() => removeFile(i)}
                aria-label={`Remove ${af.file.name}`}
                className="text-[var(--text-tertiary)] hover:text-[var(--danger)]"
              >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Input area */}
      <div className="max-w-3xl mx-auto px-4 py-3">
        <div className="flex items-end gap-2 rounded-xl border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2 focus-within:border-[var(--accent)] transition-colors">
          {/* Attach button */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setShowAttach(!showAttach)}
              disabled={disabled}
              aria-label="Attach file"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md text-[var(--text-tertiary)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-secondary)] transition-colors disabled:opacity-50"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l8.57-8.57A4 4 0 1 1 18 8.84l-8.59 8.57a2 2 0 0 1-2.83-2.83l8.49-8.48" />
              </svg>
            </button>
            {showAttach && (
              <div className="absolute bottom-full left-0 mb-2 w-52 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] shadow-lg p-1 z-10">
                <button
                  type="button"
                  onClick={() => fileRef.current?.click()}
                  className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-xs text-[var(--text-secondary)] hover:bg-[var(--bg-hover)] hover:text-[var(--text-primary)]"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z" />
                    <polyline points="14 2 14 8 20 8" />
                  </svg>
                  Upload file
                </button>
                <div className="px-3 py-1 text-[10px] text-[var(--text-tertiary)]">
                  PDF, DOCX, TXT, code files
                </div>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept=".txt,.md,.pdf,.docx" multiple onChange={handleFileSelect} className="hidden" />

          {/* Textarea */}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            placeholder="Message SafeAgent..."
            aria-label="Message input"
            disabled={disabled}
            rows={1}
            className="flex-1 resize-none bg-transparent text-[13px] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] outline-none py-1 leading-relaxed disabled:opacity-50"
          />

          {/* Send / Stop */}
          {isStreaming ? (
            <button
              type="button"
              onClick={onStop}
              aria-label="Stop generation"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--danger)] text-white hover:bg-red-600 transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
            </button>
          ) : (
            <button
              type="submit"
              disabled={disabled || !input.trim()}
              aria-label="Send message"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
                <path d="M5 12l14-7-7 14v-7z" />
              </svg>
            </button>
          )}
        </div>

        {/* Character count */}
        <div className="flex justify-end mt-1">
          <span className="text-[10px] text-[var(--text-tertiary)]">
            {input.length > 0 ? `${input.length} / 10,000` : ""}
          </span>
        </div>
      </div>
    </form>
  );
}
