import type { ChatMessage } from "./api";

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

const STORAGE_KEY = "adaptiveagent_conversations";
const MAX_CONVERSATIONS = 100;

function safeGet<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    if (raw === null) return fallback;
    return JSON.parse(raw) as T;
  } catch {
    return fallback;
  }
}

function safeSet(key: string, value: unknown): void {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Storage full or unavailable
  }
}

export function getConversations(): Conversation[] {
  return safeGet<Conversation[]>(STORAGE_KEY, []);
}

export function getConversation(id: string): Conversation | undefined {
  return getConversations().find((c) => c.id === id);
}

export function saveConversation(conv: Conversation): void {
  const all = getConversations();
  const idx = all.findIndex((c) => c.id === conv.id);
  if (idx >= 0) {
    all[idx] = conv;
  } else {
    all.unshift(conv);
  }
  if (all.length > MAX_CONVERSATIONS) all.length = MAX_CONVERSATIONS;
  safeSet(STORAGE_KEY, all);
}

export function deleteConversation(id: string): void {
  const all = getConversations().filter((c) => c.id !== id);
  safeSet(STORAGE_KEY, all);
}

export function renameConversation(id: string, title: string): void {
  const all = getConversations();
  const conv = all.find((c) => c.id === id);
  if (conv) {
    conv.title = title;
    safeSet(STORAGE_KEY, all);
  }
}

export function generateTitle(content: string): string {
  const cleaned = content.replace(/\n+/g, " ").trim();
  return cleaned.length > 60 ? cleaned.slice(0, 57) + "..." : cleaned;
}

export function createConversation(id: string, firstMessage?: string): Conversation {
  const now = Date.now();
  const conv: Conversation = {
    id,
    title: firstMessage ? generateTitle(firstMessage) : "New conversation",
    messages: [],
    createdAt: now,
    updatedAt: now,
  };
  saveConversation(conv);
  return conv;
}
