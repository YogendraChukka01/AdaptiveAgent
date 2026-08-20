export interface AppSettings {
  apiBaseUrl: string;
  apiKey: string;
  modelName: string;
  theme: "light" | "dark" | "system";
  enterToSend: boolean;
  compactMode: boolean;
}

const SETTINGS_KEY = "adaptiveagent_settings";

const DEFAULTS: AppSettings = {
  apiBaseUrl: "",
  apiKey: "",
  modelName: "",
  theme: "dark",
  enterToSend: true,
  compactMode: false,
};

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

export function getSettings(): AppSettings {
  return { ...DEFAULTS, ...safeGet<AppSettings>(SETTINGS_KEY, DEFAULTS) };
}

export function updateSettings(partial: Partial<AppSettings>): AppSettings {
  const current = getSettings();
  const updated = { ...current, ...partial };
  safeSet(SETTINGS_KEY, updated);
  return updated;
}

export function resetSettings(): AppSettings {
  safeSet(SETTINGS_KEY, DEFAULTS);
  return { ...DEFAULTS };
}

export function buildApiUrl(
  baseUrl: string,
  path: string,
): string {
  const trimmed = baseUrl.replace(/\/+$/, "");
  const cleanPath = path.startsWith("/") ? path : `/${path}`;
  return `${trimmed}${cleanPath}`;
}

export function testApiConnection(
  baseUrl: string,
  apiKey: string,
): Promise<{ ok: boolean; error?: string }> {
  const url = buildApiUrl(baseUrl, "/health");
  return fetch(url, {
    method: "GET",
    headers: apiKey ? { "X-API-Key": apiKey } : {},
    signal: AbortSignal.timeout(10000),
  })
    .then((res) => {
      if (res.ok) return { ok: true };
      return { ok: false, error: `HTTP ${res.status}` };
    })
    .catch((err) => ({
      ok: false,
      error: err instanceof Error ? err.message : "Connection failed",
    }));
}
