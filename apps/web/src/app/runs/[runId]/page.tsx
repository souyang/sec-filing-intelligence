"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";

import { getRun, type WorkflowRunSummary } from "@/lib/api";
import { useRunSse } from "@/hooks/use-run-sse";

export default function RunDetailPage({
  params,
}: {
  params: Promise<{ runId: string }>;
}) {
  const { runId } = use(params);
  const { events, connected, latestCounters } = useRunSse(runId);
  const [run, setRun] = useState<WorkflowRunSummary | null>(null);

  useEffect(() => {
    getRun(runId).then(setRun).catch(() => setRun(null));
    const id = setInterval(() => getRun(runId).then(setRun).catch(() => {}), 3000);
    return () => clearInterval(id);
  }, [runId]);

  const completed = latestCounters?.completed ?? run?.completed_filings ?? 0;
  const failed = latestCounters?.failed ?? run?.failed_filings ?? 0;
  const reviewPending = latestCounters?.review_pending ?? run?.review_pending ?? 0;
  const total = run?.total_filings ?? 0;
  const inProgress = latestCounters?.in_progress ?? Math.max(0, total - completed - failed - reviewPending);
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center gap-4">
          <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-100">
            ← Back
          </Link>
          <h1 className="text-lg font-semibold">Run {runId.slice(0, 8)}…</h1>
          <span className="text-sm text-zinc-500">{run?.status ?? "—"}</span>
          <span
            className={`ml-auto text-xs rounded-full px-2 py-0.5 ${
              connected ? "bg-emerald-900 text-emerald-300" : "bg-zinc-800 text-zinc-400"
            }`}
          >
            SSE {connected ? "live" : "offline"}
          </span>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-8 space-y-6">
        <div className="rounded-xl border border-zinc-800 p-4">
          <div className="flex justify-between text-sm text-zinc-400 mb-2">
            <span>Throughput</span>
            <span>{pct}% ({completed}/{total})</span>
          </div>
          <div className="h-2 rounded-full bg-zinc-800 overflow-hidden">
            <div
              className="h-full bg-emerald-500 transition-all"
              style={{ width: `${pct}%` }}
            />
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-4">
          {[
            ["Completed", completed],
            ["Failed", failed],
            ["Review", reviewPending],
            ["In progress", inProgress],
          ].map(([label, val]) => (
            <div key={label as string} className="rounded-xl border border-zinc-800 p-4">
              <dt className="text-xs text-zinc-500">{label}</dt>
              <dd className="text-2xl font-semibold mt-1">{val}</dd>
            </div>
          ))}
        </div>

        <section className="rounded-xl border border-zinc-800 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Event log</h2>
          <ul className="max-h-80 overflow-y-auto space-y-2 font-mono text-xs">
            {events.length === 0 && (
              <li className="text-zinc-500">Waiting for Redis stream events…</li>
            )}
            {events.map((ev, i) => (
              <li key={i} className="rounded bg-zinc-900 px-2 py-1 text-zinc-300">
                <span className="text-emerald-600">{ev.type ?? "event"}</span>{" "}
                {ev.stage && `stage=${ev.stage} `}
                {ev.status && `status=${ev.status}`}
                {ev.completed !== undefined && `c=${ev.completed} f=${ev.failed}`}
              </li>
            ))}
          </ul>
        </section>
      </main>
    </div>
  );
}
