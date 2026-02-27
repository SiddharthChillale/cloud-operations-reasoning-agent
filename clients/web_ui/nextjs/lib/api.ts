import {
  Session,
  SessionWithMessages,
  CreateSessionResponse,
  DeleteSessionResponse,
  UpdateSessionResponse,
  SSEMessage,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      Accept: "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(error.error || `HTTP error ${response.status}`);
  }

  return response.json();
}

export async function getSessions(): Promise<Session[]> {
  const result = await fetchJSON<{ sessions: Session[] }>(
    `${API_BASE}/sessions`
  );
  return result.sessions;
}

export async function createSession(title?: string): Promise<CreateSessionResponse> {
  return fetchJSON<CreateSessionResponse>(`${API_BASE}/sessions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title: title || "New Chat" }),
  });
}

export async function getSession(sessionId: string): Promise<SessionWithMessages> {
  return fetchJSON<SessionWithMessages>(`${API_BASE}/sessions/${sessionId}`);
}

export async function updateSessionTitle(
  sessionId: string,
  title: string
): Promise<UpdateSessionResponse> {
  return fetchJSON<UpdateSessionResponse>(`${API_BASE}/sessions/${sessionId}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ title }),
  });
}

export async function deleteSession(sessionId: string): Promise<DeleteSessionResponse> {
  return fetchJSON<DeleteSessionResponse>(`${API_BASE}/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export async function getTokens(sessionId: string) {
  const result = await fetchJSON<{ tokens: any }>(
    `${API_BASE}/sessions/${sessionId}/tokens`
  );
  return result.tokens;
}

export async function* streamChat(
  sessionId: string,
  query: string
): AsyncGenerator<SSEMessage, void, unknown> {
  const url = `${API_BASE}/sessions/${sessionId}/stream?${new URLSearchParams({
    query,
  })}`;

  console.log("[streamChat] Starting stream to:", url);

  const response = await fetch(url);

  console.log("[streamChat] Response status:", response.status);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: "Unknown error" }));
    console.error("[streamChat] Error response:", error);
    throw new Error(error.error || `HTTP error ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Response body is null");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        const data = line.slice(6);
        try {
          const event = JSON.parse(data) as SSEMessage;
          console.log("[streamChat] Received event:", event.type, event.step_number, event.step_type);
          yield event;
          if (event.type === "done" || event.type === "error") {
            return;
          }
        } catch (e) {
          console.error("[streamChat] Failed to parse SSE event:", data);
        }
      }
    }
  }
}
