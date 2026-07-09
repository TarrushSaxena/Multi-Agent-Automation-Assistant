import { LucideIcon } from "lucide-react";

type Props = {
  label: string;
  value: string;
  icon: LucideIcon;
  tone?: "default" | "success" | "warning" | "danger";
};

const TONE_COLOR: Record<NonNullable<Props["tone"]>, string> = {
  default: "var(--accent)",
  success: "var(--success)",
  warning: "var(--warning)",
  danger: "var(--danger)"
};

export function StatTile({ label, value, icon: Icon, tone = "default" }: Props) {
  const color = TONE_COLOR[tone];
  return (
    <div className="glass glass-rim rounded-2xl p-4 transition hover:-translate-y-0.5">
      <div className="flex items-center gap-2 text-xs font-medium text-[var(--text-muted)]">
        <span
          className="grid h-6 w-6 place-items-center rounded-lg"
          style={{ background: `color-mix(in srgb, ${color} 16%, transparent)`, color }}
        >
          <Icon className="h-3.5 w-3.5" />
        </span>
        {label}
      </div>
      <p className="font-display mt-2.5 font-mono-tabular text-2xl font-semibold text-[var(--text-primary)]">{value}</p>
    </div>
  );
}
