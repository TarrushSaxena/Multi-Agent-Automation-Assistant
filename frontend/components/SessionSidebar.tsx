"use client";

import { MessageSquarePlus, Trash2 } from "lucide-react";
import { deleteSession } from "../lib/api";
import { useSessions } from "../lib/hooks/useSessions";
import { BrandLogo } from "./BrandLogo";
import { ThemeToggle } from "./ThemeToggle";

type Props = {
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
};

function relativeTime(iso: string): string {
  const diffMs = Date.now() - new Date(iso + "Z").getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function SessionSidebar({ activeSessionId, onSelectSession, onNewChat }: Props) {
  const { data: sessions = [], mutate } = useSessions();

  return (
    <aside className="glass relative z-10 flex flex-col border-y-0 border-l-0">
      <div className="flex items-center gap-3 border-b border-[var(--border)] px-4 py-4">
        <div className="glass-rim grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-[var(--surface-2)]">
          <BrandLogo className="h-6 w-6" />
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="font-display truncate text-[15px] font-semibold tracking-tight text-[var(--text-primary)]">
            Automation Assistant
          </h1>
          <p className="truncate text-xs text-[var(--text-muted)]">Agentic multi-step co-pilot</p>
        </div>
        <ThemeToggle />
      </div>

      <div className="px-4 py-4">
        <button
          type="button"
          onClick={onNewChat}
          className="glass-rim flex w-full items-center justify-center gap-2 rounded-2xl bg-[var(--accent-soft)] px-3 py-2.5 text-sm font-medium text-[var(--text-primary)] transition hover:bg-[color-mix(in_srgb,var(--accent)_22%,transparent)]"
        >
          <MessageSquarePlus className="h-4 w-4 text-[var(--accent)]" />
          New chat
        </button>
      </div>

      <div className="scrollbar-thin flex-1 space-y-1.5 overflow-y-auto px-4 pb-4">
        {sessions.length === 0 && (
          <p className="rounded-2xl border border-dashed border-[var(--border)] px-3 py-6 text-center text-xs text-[var(--text-muted)]">
            No conversations yet. Ask something to start one.
          </p>
        )}
        {sessions.map((session) => (
          <div
            key={session.id}
            onClick={() => onSelectSession(session.id)}
            className={`group flex cursor-pointer items-center justify-between gap-2 rounded-2xl border px-3 py-2.5 transition ${
              session.id === activeSessionId
                ? "border-[var(--accent-border)] bg-[var(--accent-soft)] shadow-[var(--shadow-glow)]"
                : "border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_50%,transparent)] hover:border-[var(--border-strong)]"
            }`}
          >
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-[var(--text-primary)]">{session.preview}</p>
              <p className="mt-0.5 text-xs text-[var(--text-muted)]">{relativeTime(session.created_at)}</p>
            </div>
            <button
              type="button"
              title="Delete conversation"
              onClick={async (event) => {
                event.stopPropagation();
                await deleteSession(session.id);
                if (session.id === activeSessionId) onNewChat();
                mutate();
              }}
              className="rounded-lg p-1 text-[var(--text-muted)] opacity-0 transition group-hover:opacity-100 hover:bg-[var(--danger-soft)] hover:text-[var(--danger)]"
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>
        ))}
      </div>
    </aside>
  );
}
