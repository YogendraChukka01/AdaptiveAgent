const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  response: string;
  citations: Array<{
    source: string;
    chunk: string;
    relevance_score: number;
  }>;
  confidence_score: number;
  risk_score: number;
  risk_level: string;
  reasoning_path: string[];
  step_count: number;
}

export async function* streamChat(
  messages: ChatMessage[],
  threadId: string,
): AsyncGenerator<string, ChatResult> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      thread_id: threadId,
      stream: true,
    }),
  });

  if (!response.ok) throw new Error(`Chat failed: ${response.status}`);

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("event: token\ndata: ")) {
        const data = JSON.parse(line.replace("event: token\ndata: ", ""));
        yield data.token;
      } else if (line.startsWith("event: complete\ndata: ")) {
        const data = JSON.parse(line.replace("event: complete\ndata: ", ""));
        return {
          response: data.response,
          citations: data.citations || [],
          confidence_score: data.confidence_score,
          risk_score: data.risk_score,
          risk_level: data.risk_level,
          reasoning_path: data.reasoning_path,
          step_count: data.step_count,
        } as ChatResult;
      } else if (line.startsWith("event: done")) {
        return {
          response: "",
          citations: [],
          confidence_score: 0,
          risk_score: 0,
          risk_level: "low",
          reasoning_path: [],
          step_count: 0,
        } as ChatResult;
      }
    }
  }

  return {
    response: "",
    citations: [],
    confidence_score: 0,
    risk_score: 0,
    risk_level: "low",
    reasoning_path: [],
    step_count: 0,
  } as ChatResult;
}

export async function sendMessage(
  messages: ChatMessage[],
  threadId: string,
): Promise<ChatResult> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      thread_id: threadId,
      stream: false,
    }),
  });

  if (!response.ok) throw new Error(`Chat failed: ${response.status}`);
  return response.json();
}

export async function uploadDocument(
  file: File,
  threadId: string = "default",
): Promise<{ filename: string; chunks: number }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("thread_id", threadId);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) throw new Error(`Upload failed: ${response.status}`);
  return response.json();
}

export async function approveAction(
  threadId: string,
  action: "approve" | "reject",
): Promise<{ status: string; response: string }> {
  const response = await fetch(`${API_BASE}/chat/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, action }),
  });

  if (!response.ok) throw new Error(`Approval failed: ${response.status}`);
  return response.json();
}

export async function getAuditLogs(
  limit = 50,
  threadId?: string,
): Promise<any[]> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (threadId) params.set("thread_id", threadId);

  const response = await fetch(`${API_BASE}/audit?${params}`);
  if (!response.ok) throw new Error(`Audit failed: ${response.status}`);
  return response.json();
}
