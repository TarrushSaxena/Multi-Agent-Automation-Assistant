const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export type PendingApproval = {
  tool_call_id: string;
  tool_name: string;
  args: Record<string, unknown>;
};

export type StreamResult = {
  session_id: string;
  message_id?: string;
  status: "complete" | "awaiting_approval";
  pending?: PendingApproval;
};

export type SessionSummary = {
  id: string;
  created_at: string;
  preview: string;
};

export type StoredMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type ToolCallRecord = {
  id: string;
  session_id: string;
  tool_name: string;
  arguments: Record<string, unknown>;
  is_sensitive: boolean;
  status: string;
  requested_at: string;
  approved_by: string | null;
  approved_at: string | null;
  executed_at: string | null;
  result: Record<string, unknown> | null;
  error: string | null;
};

export type AuditResponse = {
  items: ToolCallRecord[];
  summary: { total: number; pending: number; executed: number; denied: number; failed: number };
};

async function consumeStream(response: Response, onToken: (t: string) => void): Promise<StreamResult> {
  if (!response.ok || !response.body) throw new Error("Request failed");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: StreamResult | null = null;
  let pending: PendingApproval | undefined;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const line = event.split("\n").find((item) => item.startsWith("data: "));
      if (!line) continue;
      const payload = JSON.parse(line.slice(6));
      if (payload.type === "token") onToken(payload.value);
      if (payload.type === "pending_approval") {
        pending = { tool_call_id: payload.tool_call_id, tool_name: payload.tool_name, args: payload.args };
      }
      if (payload.type === "done") {
        result = {
          session_id: payload.session_id,
          message_id: payload.message_id,
          status: payload.status,
          pending
        };
      }
    }
  }
  if (!result) throw new Error("Stream ended without a done event");
  return result;
}

export async function streamChat(
  message: string,
  sessionId: string | null,
  onToken: (token: string) => void
): Promise<StreamResult> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  return consumeStream(response, onToken);
}

export async function decideToolCall(
  toolCallId: string,
  decision: "approve" | "deny",
  onToken: (token: string) => void
): Promise<StreamResult> {
  const response = await fetch(`${API_BASE}/chat/approvals/${toolCallId}/${decision}`, { method: "POST" });
  return consumeStream(response, onToken);
}

export async function fetchSessions(): Promise<SessionSummary[]> {
  const response = await fetch(`${API_BASE}/chat/sessions`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load sessions");
  return response.json();
}

export async function fetchSessionMessages(sessionId: string): Promise<StoredMessage[]> {
  const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}/messages`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load session");
  return response.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/sessions/${sessionId}`, { method: "DELETE" });
  if (!response.ok) throw new Error("Failed to delete session");
}

export async function fetchAudit(): Promise<AuditResponse> {
  const response = await fetch(`${API_BASE}/audit`, { cache: "no-store" });
  if (!response.ok) throw new Error("Failed to load audit log");
  return response.json();
}
