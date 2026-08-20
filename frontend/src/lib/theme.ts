type Theme = "light" | "dark" | "system";

const THEME_KEY = "adaptiveagent_theme";

function safeGet(key: string, fallback: string): string {
  try {
    return localStorage.getItem(key) ?? fallback;
  } catch {
    return fallback;
  }
}

function safeSet(key: string, value: string): void {
  try {
    localStorage.setItem(key, value);
  } catch {
    // Storage unavailable
  }
}

function getSystemPreference(): "light" | "dark" {
  if (typeof window === "undefined") return "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function getStoredTheme(): Theme {
  return safeGet(THEME_KEY, "dark") as Theme;
}

export function resolveTheme(theme: Theme): "light" | "dark" {
  return theme === "system" ? getSystemPreference() : theme;
}

export function applyTheme(theme: Theme): void {
  const resolved = resolveTheme(theme);
  const root = document.documentElement;
  root.classList.remove("light", "dark");
  root.classList.add(resolved);
  root.setAttribute("data-theme", resolved);
}

export function setTheme(theme: Theme): void {
  safeSet(THEME_KEY, theme);
  applyTheme(theme);
}

export function initTheme(): Theme {
  const stored = getStoredTheme();
  applyTheme(stored);
  return stored;
}

export function watchSystemTheme(callback: (theme: "light" | "dark") => void): () => void {
  if (typeof window === "undefined") return () => {};
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  const handler = (e: MediaQueryListEvent) => callback(e.matches ? "dark" : "light");
  mq.addEventListener("change", handler);
  return () => mq.removeEventListener("change", handler);
}
