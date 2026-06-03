"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { listReviewTasks, submitReviewDecision, type ReviewTask } from "@/lib/api";

export default function ReviewPage() {
  const [tasks, setTasks] = useState<ReviewTask[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ReviewTask | null>(null);
  const [note, setNote] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setTasks(await listReviewTasks());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [load]);

  async function decide(action: "approve" | "reject") {
    if (!selected) return;
    setSubmitting(true);
    try {
      await submitReviewDecision(selected.id, action, note || undefined);
      setSelected(null);
      setNote("");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Submit failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-6xl items-center gap-4">
          <Link href="/" className="text-sm text-zinc-400 hover:text-zinc-100">
            ← Back
          </Link>
          <h1 className="text-lg font-semibold">Reviewer queue</h1>
          <span className="ml-auto text-sm text-zinc-500">{tasks.length} pending</span>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8 grid gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-zinc-800 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Pending tasks</h2>
          {loading && <p className="text-zinc-500 text-sm">Loading…</p>}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <ul className="space-y-2">
            {tasks.map((t) => (
              <li key={t.id}>
                <button
                  type="button"
                  onClick={() => setSelected(t)}
                  className={`w-full text-left rounded-lg px-3 py-2 text-sm border ${
                    selected?.id === t.id
                      ? "border-emerald-600 bg-emerald-950/30"
                      : "border-zinc-800 hover:border-zinc-600"
                  }`}
                >
                  <span className="font-medium">{t.ticker ?? "—"}</span>
                  <span className="text-zinc-500 ml-2">
                    confidence {(t.confidence ?? 0).toFixed(2)}
                  </span>
                </button>
              </li>
            ))}
            {!loading && tasks.length === 0 && (
              <p className="text-zinc-500 text-sm">No pending reviews.</p>
            )}
          </ul>
        </section>

        <section className="rounded-xl border border-zinc-800 p-4">
          <h2 className="text-sm font-medium text-zinc-400 mb-3">Inspection</h2>
          {!selected && <p className="text-zinc-500 text-sm">Select a task.</p>}
          {selected && (
            <div className="space-y-4">
              <pre className="max-h-64 overflow-auto rounded bg-zinc-900 p-3 text-xs text-zinc-300">
                {JSON.stringify(selected.payload, null, 2)}
              </pre>
              <textarea
                className="w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2 text-sm"
                placeholder="Reviewer note (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => decide("approve")}
                  className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
                >
                  Approve
                </button>
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => decide("reject")}
                  className="rounded-lg bg-red-800 px-4 py-2 text-sm font-medium hover:bg-red-700 disabled:opacity-50"
                >
                  Reject
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
