import { CalendarPlus, Check, Mail, ShieldAlert, X } from "lucide-react";
import { PendingApproval } from "../lib/api";

type Props = {
  pending: PendingApproval;
  disabled?: boolean;
  onApprove: () => void;
  onDeny: () => void;
};

function humanSummary(pending: PendingApproval): { icon: typeof Mail; title: string; rows: [string, string][] } {
  const args = pending.args as Record<string, string | string[]>;
  if (pending.tool_name === "send_email") {
    return {
      icon: Mail,
      title: "Send email",
      rows: [
        ["To", String(args.to ?? "")],
        ["Subject", String(args.subject ?? "")],
        ["Body", String(args.body ?? "")]
      ]
    };
  }
  if (pending.tool_name === "create_calendar_event") {
    const attendees = Array.isArray(args.attendees) ? args.attendees.join(", ") : String(args.attendees ?? "");
    return {
      icon: CalendarPlus,
      title: "Create calendar event",
      rows: [
        ["Title", String(args.summary ?? "")],
        ["Start", String(args.start ?? "")],
        ["End", String(args.end ?? "")],
        ["Attendees", attendees || "—"]
      ]
    };
  }
  return {
    icon: ShieldAlert,
    title: pending.tool_name,
    rows: Object.entries(args).map(([k, v]) => [k, String(v)] as [string, string])
  };
}

export function PendingApprovalCard({ pending, disabled, onApprove, onDeny }: Props) {
  const { icon: Icon, title, rows } = humanSummary(pending);
  return (
    <div
      className="glass-strong animate-fade-up relative overflow-hidden rounded-3xl p-4"
      style={{ boxShadow: "var(--shadow-md), inset 0 1px 0 var(--glass-highlight), 0 0 40px -18px var(--warning)" }}
    >
      <span
        className="pointer-events-none absolute inset-x-0 top-0 h-px"
        style={{ background: "linear-gradient(90deg, transparent, var(--warning), transparent)" }}
      />
      <div className="flex items-center gap-2 text-sm font-semibold text-[var(--text-primary)]">
        <span className="grid h-7 w-7 place-items-center rounded-lg bg-[var(--warning-soft)] text-[var(--warning)]">
          <Icon className="h-4 w-4" />
        </span>
        Approval required
        <span className="text-[var(--text-muted)]">— {title}</span>
      </div>
      <dl className="mt-3 space-y-1.5 text-sm">
        {rows.map(([label, value]) => (
          <div key={label} className="flex gap-2">
            <dt className="w-20 shrink-0 text-xs font-medium uppercase tracking-wide text-[var(--text-muted)]">
              {label}
            </dt>
            <dd className="min-w-0 flex-1 whitespace-pre-wrap break-words text-[var(--text-secondary)]">{value}</dd>
          </div>
        ))}
      </dl>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          disabled={disabled}
          onClick={onApprove}
          className="inline-flex items-center gap-1.5 rounded-xl px-3.5 py-2 text-xs font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-40"
          style={{ background: "linear-gradient(135deg, var(--success), color-mix(in srgb, var(--success) 70%, var(--aurora-3)))" }}
        >
          <Check className="h-3.5 w-3.5" />
          Approve
        </button>
        <button
          type="button"
          disabled={disabled}
          onClick={onDeny}
          className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_50%,transparent)] px-3.5 py-2 text-xs font-semibold text-[var(--text-secondary)] transition hover:border-[var(--danger)] hover:text-[var(--danger)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          <X className="h-3.5 w-3.5" />
          Deny
        </button>
      </div>
    </div>
  );
}
