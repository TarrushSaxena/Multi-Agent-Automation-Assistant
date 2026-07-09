"use client";

import { CalendarPlus, CornerDownLeft, Mail, ScrollText, Search, Trash2 } from "lucide-react";
import Link from "next/link";
import { FormEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useChat } from "../lib/hooks/useChat";
import { BrandLogo } from "./BrandLogo";
import { MessageBubble } from "./MessageBubble";

const SUGGESTIONS = [
  { icon: Search, text: "Search the web for the latest on our top competitor and summarize it" },
  { icon: Mail, text: "Draft and send a project kickoff email to the team" },
  { icon: CalendarPlus, text: "Schedule a follow-up meeting next Monday at 10am" }
];

export function ChatWindow({ chat, onNewChat }: { chat: ReturnType<typeof useChat>; onNewChat: () => void }) {
  const [question, setQuestion] = useState("");
  const { messages, isStreaming, send, decide } = chat;
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [question]);

  async function submit(value: string) {
    if (!value.trim() || isStreaming) return;
    setQuestion("");
    await send(value.trim());
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    await submit(question);
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      submit(question);
    }
  }

  return (
    <main className="relative flex min-h-0 flex-col">
      <header className="glass-strong relative z-10 flex items-center justify-between gap-4 border-x-0 border-t-0 px-6 py-3.5">
        <div>
          <h2 className="font-display text-[15px] font-semibold text-[var(--text-primary)]">Assistant</h2>
          <p className="text-xs text-[var(--text-muted)]">Plans and executes multi-step workflows across your tools</p>
        </div>
        <div className="flex items-center gap-2">
          <Link
            href="/audit"
            title="Activity log"
            className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_50%,transparent)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]"
          >
            <ScrollText className="h-3.5 w-3.5" />
            Activity
          </Link>
          <button
            type="button"
            onClick={onNewChat}
            className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_50%,transparent)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]"
          >
            <Trash2 className="h-3.5 w-3.5" />
            New chat
          </button>
        </div>
      </header>

      <div ref={scrollRef} className="scrollbar-thin flex-1 overflow-y-auto">
        <div className="mx-auto flex min-h-full max-w-[780px] flex-col justify-end px-6 py-8">
          {messages.length === 0 ? (
            <div className="animate-fade-up flex flex-1 flex-col items-center justify-center gap-7 text-center">
              <div className="glass-strong glass-rim grid h-20 w-20 place-items-center rounded-[1.6rem]">
                <BrandLogo className="h-11 w-11" />
              </div>
              <div>
                <h1 className="font-display text-4xl font-semibold tracking-tight sm:text-5xl">
                  <span className="text-gradient">What should we get done?</span>
                </h1>
                <p className="mx-auto mt-3 max-w-md text-sm leading-6 text-[var(--text-secondary)]">
                  Describe a goal in plain language. I&apos;ll plan the steps, use tools, and pause for your approval
                  before anything is sent.
                </p>
              </div>
              <div className="grid w-full max-w-lg gap-2.5">
                {SUGGESTIONS.map(({ icon: Icon, text }) => (
                  <button
                    key={text}
                    type="button"
                    onClick={() => submit(text)}
                    className="glass glass-rim group flex items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-[var(--text-secondary)] transition hover:-translate-y-0.5 hover:text-[var(--text-primary)]"
                  >
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-xl bg-[var(--accent-soft)] text-[var(--accent)]">
                      <Icon className="h-4 w-4" />
                    </span>
                    {text}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((message, index) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  streaming={isStreaming && index === messages.length - 1 && message.role === "assistant"}
                  decisionPending={isStreaming}
                  onDecide={decide}
                />
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="relative z-10 px-6 pb-6 pt-2">
        <form onSubmit={onSubmit} className="mx-auto max-w-[780px]">
          <div className="glass-strong glass-rim flex items-end gap-2 rounded-[1.4rem] p-2 transition focus-within:animate-glow">
            <textarea
              ref={textareaRef}
              rows={1}
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={onKeyDown}
              className="max-h-40 flex-1 resize-none bg-transparent px-3 py-2.5 text-[15px] text-[var(--text-primary)] outline-none placeholder:text-[var(--text-muted)]"
              placeholder="Describe a goal, e.g. “Summarize last week's notes and email the team”…"
            />
            <button
              type="submit"
              title="Send"
              disabled={isStreaming || !question.trim()}
              className="brand-mark grid h-10 w-10 shrink-0 place-items-center rounded-2xl text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40 disabled:saturate-50"
            >
              <CornerDownLeft className="h-4 w-4" />
            </button>
          </div>
          <p className="mt-2.5 text-center text-xs text-[var(--text-muted)]">
            <span className="font-medium text-[var(--text-secondary)]">Enter</span> to send ·{" "}
            <span className="font-medium text-[var(--text-secondary)]">Shift + Enter</span> for a new line
          </p>
        </form>
      </div>
    </main>
  );
}
