"use client";

import { useEffect, useState } from "react";

interface WelcomeScreenProps {
  onSuggestion: (text: string) => void;
}

const SUGGESTIONS = [
  { icon: "M12 2L2 7l10 5 10-5-10-5z", label: "Build an AI Agent", prompt: "Help me build an AI agent that can browse the web and perform tasks autonomously." },
  { icon: "M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z", label: "Analyze a Repository", prompt: "Analyze the codebase in this repository and suggest improvements for architecture, performance, and code quality." },
  { icon: "M12 20h9M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z", label: "Debug Code", prompt: "I have a bug in my code. Help me debug it step by step." },
  { icon: "M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z", label: "Design a Product", prompt: "Help me design a product feature from concept to implementation details." },
  { icon: "M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z", label: "Explain a Concept", prompt: "Explain a complex technical concept to me in simple terms with examples." },
  { icon: "M9 11l3 3L22 4M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11", label: "Plan a Project", prompt: "Help me plan a software project with milestones, tech stack decisions, and architecture." },
];

function getGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 17) return "Good afternoon";
  return "Good evening";
}

export function WelcomeScreen({ onSuggestion }: WelcomeScreenProps) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 50);
    return () => clearTimeout(t);
  }, []);

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 pb-24">
      <div className={`max-w-md text-center transition-all duration-500 ${visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"}`}>
        <h1 className="text-2xl font-semibold tracking-tight mb-1">
          {getGreeting()}
        </h1>
        <p className="text-sm text-[var(--text-secondary)] mb-8">
          What would you like to explore?
        </p>

        <div className="grid grid-cols-2 gap-2.5">
          {SUGGESTIONS.map((s, i) => (
            <button
              key={s.label}
              onClick={() => onSuggestion(s.prompt)}
              className={`flex items-start gap-2.5 rounded-lg border border-[var(--border)] bg-[var(--bg-secondary)] px-3 py-2.5 text-left text-xs transition-all hover:bg-[var(--bg-hover)] hover:border-[var(--text-tertiary)] ${
                visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-2"
              }`}
              style={{ transitionDelay: `${100 + i * 50}ms` }}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="mt-0.5 shrink-0 text-[var(--text-tertiary)]">
                <path d={s.icon} />
              </svg>
              <span className="text-[var(--text-primary)] font-medium">{s.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
