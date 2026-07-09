import { Sparkles, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../lib/hooks/useChat";
import { PendingApprovalCard } from "./PendingApprovalCard";

type Props = {
  message: ChatMessage;
  streaming?: boolean;
  decisionPending?: boolean;
  onDecide?: (assistantId: string, toolCallId: string, decision: "approve" | "deny") => void;
};

export function MessageBubble({ message, streaming, decisionPending, onDecide }: Props) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <article className="animate-fade-up flex items-start justify-end gap-3">
        <div
          className="max-w-[80%] rounded-3xl rounded-tr-md px-4 py-2.5 text-white shadow-[var(--shadow-glow)]"
          style={{ background: "linear-gradient(135deg, var(--aurora-4), var(--accent) 55%, var(--aurora-2))" }}
        >
          <p className="whitespace-pre-wrap text-[15px] leading-6">{message.content}</p>
        </div>
        <div className="mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full border border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_60%,transparent)] text-[var(--text-secondary)]">
          <User className="h-4 w-4" />
        </div>
      </article>
    );
  }

  return (
    <article className="animate-fade-up flex items-start gap-3">
      <div className="brand-mark mt-0.5 grid h-8 w-8 shrink-0 place-items-center rounded-full text-white">
        <Sparkles className="h-4 w-4" />
      </div>
      <div className="min-w-0 max-w-[86%] flex-1 space-y-3">
        {(message.content || streaming) && (
          <div className="glass glass-rim rounded-3xl rounded-tl-md px-4 py-3">
            <div className="prose prose-sm max-w-none text-[15px] leading-6 text-[var(--text-primary)] prose-headings:text-[var(--text-primary)] prose-strong:text-[var(--text-primary)] prose-p:my-1.5 prose-a:text-[var(--accent)]">
              {streaming && !message.content ? (
                <div className="flex items-center gap-1 py-1" aria-label="Assistant is thinking">
                  <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                  <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                  <span className="thinking-dot h-1.5 w-1.5 rounded-full bg-[var(--accent)]" />
                </div>
              ) : (
                <>
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                  {streaming && <span className="caret-blink" aria-hidden />}
                </>
              )}
            </div>
          </div>
        )}

        {message.pendingApproval && onDecide && (
          <PendingApprovalCard
            pending={message.pendingApproval}
            disabled={decisionPending}
            onApprove={() => onDecide(message.id, message.pendingApproval!.tool_call_id, "approve")}
            onDeny={() => onDecide(message.id, message.pendingApproval!.tool_call_id, "deny")}
          />
        )}
      </div>
    </article>
  );
}
