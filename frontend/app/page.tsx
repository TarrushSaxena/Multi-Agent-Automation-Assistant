"use client";

import { ChatWindow } from "../components/ChatWindow";
import { SessionSidebar } from "../components/SessionSidebar";
import { useChat } from "../lib/hooks/useChat";

export default function Home() {
  const chat = useChat();

  return (
    <div className="grid h-screen grid-cols-1 overflow-hidden md:grid-cols-[300px_minmax(0,1fr)]">
      <SessionSidebar
        activeSessionId={chat.sessionId}
        onSelectSession={chat.loadSession}
        onNewChat={chat.reset}
      />
      <ChatWindow chat={chat} onNewChat={chat.reset} />
    </div>
  );
}
