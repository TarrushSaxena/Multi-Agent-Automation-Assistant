import { ToolCallRecord } from "../lib/api";

const STATUS_TONE: Record<string, string> = {
  pending: "var(--warning)",
  approved: "var(--info)",
  executed: "var(--success)",
  denied: "var(--text-muted)",
  failed: "var(--danger)"
};

function summarizeArgs(record: ToolCallRecord): string {
  const args = record.arguments as Record<string, unknown>;
  if (record.tool_name === "send_email") return `to ${args.to} — ${args.subject}`;
  if (record.tool_name === "create_calendar_event") return `${args.summary} @ ${args.start}`;
  if (record.tool_name === "web_search") return String(args.query ?? "");
  return JSON.stringify(args);
}

export function AuditLogTable({ items }: { items: ToolCallRecord[] }) {
  return (
    <div className="glass glass-rim rounded-2xl p-4">
      <h3 className="font-display text-sm font-semibold text-[var(--text-primary)]">Tool call history</h3>
      <div className="scrollbar-thin mt-3 overflow-x-auto">
        <table className="w-full min-w-[640px] text-left text-sm">
          <thead>
            <tr className="text-xs text-[var(--text-muted)]">
              <th className="pb-2 font-medium">Tool</th>
              <th className="pb-2 font-medium">Details</th>
              <th className="pb-2 font-medium">Status</th>
              <th className="pb-2 font-medium">Requested</th>
            </tr>
          </thead>
          <tbody>
            {items.map((record) => (
              <tr key={record.id} className="border-t border-[var(--border)]">
                <td className="py-2 pr-4">
                  <span className="font-medium text-[var(--text-primary)]">{record.tool_name}</span>
                  {record.is_sensitive && (
                    <span className="ml-1.5 rounded-full bg-[var(--warning-soft)] px-1.5 py-0.5 text-[10px] font-medium text-[var(--warning)]">
                      sensitive
                    </span>
                  )}
                </td>
                <td className="max-w-xs truncate py-2 pr-4 text-[var(--text-secondary)]">{summarizeArgs(record)}</td>
                <td className="py-2 pr-4">
                  <span
                    className="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold"
                    style={{
                      color: STATUS_TONE[record.status] ?? "var(--text-secondary)",
                      background: `color-mix(in srgb, ${STATUS_TONE[record.status] ?? "var(--text-muted)"} 14%, transparent)`
                    }}
                  >
                    {record.status}
                  </span>
                  {record.error && <span className="ml-1 text-xs text-[var(--danger)]">· {record.error}</span>}
                </td>
                <td className="py-2 font-mono-tabular text-xs text-[var(--text-secondary)]">
                  {new Date(record.requested_at + "Z").toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
