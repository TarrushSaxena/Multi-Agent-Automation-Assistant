"use client";

import { ArrowLeft, CheckCircle2, Clock, ListChecks, ShieldAlert, XCircle } from "lucide-react";
import Link from "next/link";
import useSWR from "swr";
import { AuditLogTable } from "../../components/AuditLogTable";
import { StatTile } from "../../components/StatTile";
import { fetchAudit } from "../../lib/api";

export default function AuditPage() {
  const { data, isLoading } = useSWR("audit", fetchAudit, { refreshInterval: 5000 });

  return (
    <div className="min-h-screen">
      <header className="glass-strong sticky top-0 z-10 flex items-center gap-4 border-x-0 border-t-0 px-6 py-4">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 rounded-xl border border-[var(--border)] bg-[color-mix(in_srgb,var(--surface)_50%,transparent)] px-3 py-1.5 text-xs font-medium text-[var(--text-secondary)] transition hover:border-[var(--border-strong)] hover:text-[var(--text-primary)]"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          Back to chat
        </Link>
        <div>
          <h1 className="font-display text-[15px] font-semibold text-[var(--text-primary)]">Activity &amp; audit log</h1>
          <p className="text-xs text-[var(--text-muted)]">Every tool the agent proposed, with approval status</p>
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">
        {isLoading && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="skeleton h-24 rounded-2xl" />
            ))}
          </div>
        )}

        {!isLoading && data && (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              <StatTile label="Total actions" value={String(data.summary.total)} icon={ListChecks} />
              <StatTile label="Pending" value={String(data.summary.pending)} icon={Clock} tone="warning" />
              <StatTile label="Executed" value={String(data.summary.executed)} icon={CheckCircle2} tone="success" />
              <StatTile label="Denied" value={String(data.summary.denied)} icon={ShieldAlert} />
              <StatTile label="Failed" value={String(data.summary.failed)} icon={XCircle} tone="danger" />
            </div>

            {data.items.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-[var(--border)] px-6 py-16 text-center">
                <ListChecks className="mx-auto h-8 w-8 text-[var(--text-muted)]" />
                <p className="mt-3 text-sm text-[var(--text-secondary)]">
                  No tool calls yet. Ask the assistant to do something in the chat.
                </p>
              </div>
            ) : (
              <AuditLogTable items={data.items} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
