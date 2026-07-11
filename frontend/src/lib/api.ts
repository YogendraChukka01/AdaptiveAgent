const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ChatMessage {
  id?: string;
  role: "user" | "assistant";
  content: string;
}

export interface ChatResult {
  needs_approval?: boolean;
  thread_id?: string;
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
  eval_score?: number;
  eval_details?: string;
  step_count: number;
  approval_status?: string;
}

export interface ApprovalPayload {
  needs_approval: true;
  thread_id: string;
  risk_level: string | null;
  risk_score: number | null;
  approval_status: string | null;
  reason?: string | null;
  pending_tools?: string[];
  triggering_factors?: string[];
}

export type StreamEvent =
  | { type: "token"; token: string }
  | { type: "complete"; result: ChatResult }
  | { type: "needs_approval"; payload: ApprovalPayload }
  | { type: "error"; message: string };

export async function* streamChat(
  messages: ChatMessage[],
  threadId: string,
  signal?: AbortSignal,
): AsyncGenerator<StreamEvent, void> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages: messages.map((m) => ({ role: m.role, content: m.content })),
      thread_id: threadId,
      stream: true,
    }),
    signal,
  });

  if (!response.ok) {
    const messages: Record<number, string> = {
      400: "Invalid request",
      401: "Authentication required",
      403: "Access denied",
      413: "File too large",
      429: "Too many requests",
      500: "Server error",
    };
    throw new Error(messages[response.status] || `Request failed (${response.status})`);
  }

  const contentType = response.headers.get("content-type") || "";
  if (!contentType.includes("text/event-stream")) {
    const body = await response.text();
    throw new Error(`Expected SSE stream, got ${contentType}: ${body.slice(0, 200)}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No response body");

  const decoder = new TextDecoder();
  let buffer = "";
  const timeoutMs = 120_000;

  while (true) {
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      const readPromise = reader.read();
      const timeoutPromise = new Promise<never>((_, reject) => {
        timer = setTimeout(() => {
          reader.cancel().catch(() => {});
          reject(new Error("Stream timeout: no data received for 120s"));
        }, timeoutMs);
      });

      const result = await Promise.race([readPromise, timeoutPromise]) as {
        done: boolean;
        value: Uint8Array;
      };
      const { done, value } = result;
      if (done) {
        if (buffer.trim()) {
          for (const line of processBlock(buffer.trim())) {
            if (line.type === "error") {
              throw new Error(line.message);
            }
            yield line;
          }
        }
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      const blocks = buffer.split("\n\n");
      buffer = blocks.pop() || "";

      for (const block of blocks) {
        for (const evt of processBlock(block)) {
          if (evt.type === "error") {
            throw new Error(evt.message);
          }
          yield evt;
        }
      }
    } finally {
      if (timer) clearTimeout(timer);
    }
  }
}

function extractSSEData(block: string, eventPrefix: string): string | null {
  const lines = block.split("\n");
  let eventType = "";
  let dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event: ")) {
      eventType = line.slice(7).trim();
    } else if (line.startsWith("data: ")) {
      dataLines.push(line.slice(6));
    } else if (line.startsWith("id:") || line.startsWith("retry:") || line.startsWith(":")) {
      continue;
    }
  }

  if (eventType !== eventPrefix || dataLines.length === 0) return null;
  return dataLines.join("\n");
}

function processBlock(block: string): StreamEvent[] {
  const events: StreamEvent[] = [];
  try {
    const tokenData = extractSSEData(block, "token");
    if (tokenData !== null) {
      const data = JSON.parse(tokenData);
      events.push({ type: "token", token: data.token });
      return events;
    }

    const completeData = extractSSEData(block, "complete");
    if (completeData !== null) {
      const data = JSON.parse(completeData);
      events.push({
        type: "complete",
        result: {
          needs_approval: false,
          thread_id: data.thread_id,
          response: data.response,
          citations: data.citations || [],
          confidence_score: data.confidence_score,
          risk_score: data.risk_score,
          risk_level: data.risk_level,
          reasoning_path: data.reasoning_path,
          eval_score: data.eval_score,
          eval_details: data.eval_details,
          step_count: data.step_count,
          approval_status: data.approval_status,
        },
      });
      return events;
    }

    const approvalData = extractSSEData(block, "needs_approval");
    if (approvalData !== null) {
      const data = JSON.parse(approvalData);
      if (data && typeof data.thread_id === "string" && data.needs_approval === true) {
        events.push({
          type: "needs_approval",
          payload: {
            needs_approval: true,
            thread_id: data.thread_id,
            risk_level: data.risk_level ?? null,
            risk_score: data.risk_score ?? null,
            approval_status: data.approval_status ?? null,
            reason: data.reason ?? null,
            pending_tools: data.pending_tools ?? [],
            triggering_factors: data.triggering_factors ?? [],
          },
        });
      } else {
        console.warn("Invalid approval payload, skipping:", approvalData.slice(0, 100));
      }
      return events;
    }

    const errorData = extractSSEData(block, "error");
    if (errorData !== null) {
      const data = JSON.parse(errorData);
      events.push({ type: "error", message: data.error || "Stream error from server" });
      return events;
    }

    const doneData = extractSSEData(block, "done");
    if (doneData !== null) {
      return events;
    }
  } catch (err) {
    if (err instanceof SyntaxError) {
      console.warn("Malformed SSE data, skipping block:", block.slice(0, 100));
    } else {
      console.warn("SSE processing error:", err);
    }
  }
  return events;
}

export async function approveAction(
  threadId: string,
  action: "approve" | "reject",
  signal?: AbortSignal,
): Promise<ChatResult> {
  const response = await fetch(`${API_BASE}/chat/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ thread_id: threadId, action }),
    signal,
  });

  if (!response.ok) {
    const messages: Record<number, string> = {
      400: "Invalid request",
      401: "Authentication required",
      403: "Access denied",
      404: "Thread not found",
      500: "Server error",
    };
    throw new Error(messages[response.status] || `Request failed (${response.status})`);
  }
  return response.json();
}

export async function uploadDocument(
  file: File,
  threadId: string = "",
  signal?: AbortSignal,
): Promise<{ filename: string; chunks: number; total_characters: number }> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("thread_id", threadId);

  const response = await fetch(`${API_BASE}/upload`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!response.ok) {
    const messages: Record<number, string> = {
      400: "Invalid file or request",
      401: "Authentication required",
      413: "File too large",
      500: "Server error",
    };
    throw new Error(messages[response.status] || `Upload failed (${response.status})`);
  }
  return response.json();
}
