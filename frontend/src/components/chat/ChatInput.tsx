import { useState, useRef, useCallback } from "react";

interface Props {
  onSend: (content: string) => void;
  onUpload: (file: File) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, onUpload, disabled }: Props) {
  const [input, setInput] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault();
      if (input.trim() && !disabled) {
        onSend(input.trim());
        setInput("");
      }
    },
    [input, disabled, onSend],
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSubmit(e);
      }
    },
    [handleSubmit],
  );

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onUpload(file);
    },
    [onUpload],
  );

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-[var(--border)] p-4"
    >
      <div className="flex items-center gap-3 max-w-4xl mx-auto">
        <button
          type="button"
          onClick={() => fileRef.current?.click()}
          disabled={disabled}
          className="p-2 rounded-lg hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] transition-colors disabled:opacity-50"
          title="Upload document"
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
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          disabled={disabled}
          className="flex-1 bg-[var(--bg-secondary)] rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[var(--accent)] disabled:opacity-50"
        />

        <button
          type="submit"
          disabled={disabled || !input.trim()}
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
