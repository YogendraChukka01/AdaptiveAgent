import { useState, useRef, useCallback } from "react";

interface Props {
  onSend: (content: string) => void;
  onUpload: (file: File) => void;
  disabled: boolean;
}

const ACCEPTED_TYPES = new Set([
  "text/plain",
  "text/markdown",
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]);
const MAX_FILE_SIZE = 10 * 1024 * 1024;

export function ChatInput({ onSend, onUpload, disabled }: Props) {
  const [input, setInput] = useState("");
  const [fileError, setFileError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const submitIfReady = useCallback(() => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
    }
  }, [input, disabled, onSend]);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      submitIfReady();
    },
    [submitIfReady],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        submitIfReady();
      }
    },
    [submitIfReady],
  );

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      setInput(e.target.value);
      setFileError(null);
    },
    [],
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      if (!ACCEPTED_TYPES.has(file.type) && !file.name.match(/\.(txt|md|pdf|docx)$/i)) {
        setFileError("Unsupported file type. Please upload a .txt, .md, .pdf, or .docx file.");
        return;
      }
      if (file.size > MAX_FILE_SIZE) {
        setFileError("File too large. Maximum size is 10 MB.");
        return;
      }

      setFileError(null);
      onUpload(file);
      e.target.value = "";
    },
    [onUpload],
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-[var(--border)] p-4"
    >
      {fileError && (
        <div role="alert" className="max-w-4xl mx-auto mb-2 text-xs text-red-400">{fileError}</div>
      )}
      <div className="flex items-center gap-3 max-w-4xl mx-auto">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          aria-label="Upload document"
          className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] transition-colors disabled:opacity-50"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.md,.pdf,.docx"
          onChange={handleFileChange}
          className="hidden"
        />

        <input
          type="text"
          value={input}
          onChange={handleInputChange}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          aria-label="Ask a question"
          disabled={disabled}
          maxLength={10000}
          className="flex-1 bg-[var(--bg-secondary)] rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)] disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={disabled || !input.trim()}
          aria-label="Send message"
          className="p-2 rounded-lg bg-[var(--accent)] text-white hover:bg-[var(--accent-hover)] transition-colors disabled:opacity-50"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </form>
  );
}
