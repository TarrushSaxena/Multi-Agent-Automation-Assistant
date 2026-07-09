"use client";

import { useState } from "react";
import {
  decideToolCall,
  fetchSessionMessages,
  PendingApproval,
  streamChat,
  StreamResult
} from "../api";

export type ChatMessage = {
  id: string;
  backendId?: string;
  role: "user" | "assistant";
  content: string;
  pendingApproval?: PendingApproval | null;
};

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  function appendToken(assistantId: string, token: string) {
    setMessages((items) =>
      items.map((item) => (item.id === assistantId ? { ...item, content: item.content + token } : item))
    );
  }

  function applyResult(assistantId: string, result: StreamResult) {
    setSessionId(result.session_id);
    setMessages((items) =>
      items.map((item) =>
        item.id === assistantId
          ? {
              ...item,
              backendId: result.message_id ?? item.backendId,
              pendingApproval: result.status === "awaiting_approval" ? result.pending : null
            }
          : item
      )
    );
  }

  async function send(message: string) {
    const userMessage: ChatMessage = { id: crypto.randomUUID(), role: "user", content: message };
    const assistantId = crypto.randomUUID();
    setMessages((items) => [...items, userMessage, { id: assistantId, role: "assistant", content: "" }]);
    setIsStreaming(true);
    try {
      const result = await streamChat(message, sessionId, (token) => appendToken(assistantId, token));
      applyResult(assistantId, result);
    } finally {
      setIsStreaming(false);
    }
  }

  async function decide(assistantId: string, toolCallId: string, decision: "approve" | "deny") {
    // Clear the pending card and continue streaming into the same assistant bubble.
    setMessages((items) =>
      items.map((item) => (item.id === assistantId ? { ...item, pendingApproval: null } : item))
    );
    setIsStreaming(true);
    try {
      const result = await decideToolCall(toolCallId, decision, (token) => appendToken(assistantId, token));
      applyResult(assistantId, result);
    } finally {
      setIsStreaming(false);
    }
  }

  async function loadSession(id: string) {
    const stored = await fetchSessionMessages(id);
    setSessionId(id);
    setMessages(
      stored.map((m) => ({ id: m.id, backendId: m.id, role: m.role, content: m.content }))
    );
  }

  function reset() {
    setMessages([]);
    setSessionId(null);
    setIsStreaming(false);
  }

  return { messages, sessionId, isStreaming, send, decide, loadSession, reset };
}
