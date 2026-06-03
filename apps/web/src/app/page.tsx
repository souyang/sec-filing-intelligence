"use client";

import Link from "next/link";
import { useState } from "react";

import { createBatchRun, hydrateCache } from "@/lib/api";

export default function HomePage() {
  const [tickers, setTickers] = useState("AAPL,MSFT");
  const [years, setYears] = useState("2023,2024");
  const [loading, setLoading] = useState(false);
  const [hydrating, setHydrating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hitlMode, setHitlMode] = useState<"threshold_based" | "review_all" | "auto_approve_all">(
    "threshold_based",
  );

  async function startRun() {
    setLoading(true);
    setError(null);
    try {
      const result = await createBatchRun({
        filing_types: ["10-K"],
        tickers: tickers.split(",").map((t) => t.trim()).filter(Boolean),
        years: years.split(",").map((y) => parseInt(y.trim(), 10)).filter((n) => !Number.isNaN(n)),
        hitl_mode: hitlMode,
        confidence_thresholds: { default: 0.75 },
      });
      window.location.href = `/runs/${result.run_id}`;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to start run");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 px-6 py-4">
        <div className="mx-auto flex max-w-5xl items-center justify-between">
          <h1 className="text-lg font-semibold tracking-tight">SEC AlphaOps</h1>
          <nav className="flex gap-4 text-sm text-zinc-400">
            <Link href="/review" className="hover:text-zinc-100">
              Review queue
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-12">
        <p className="mb-8 max-w-2xl text-zinc-400">
          Configurable batch SEC filing intelligence. Start a 10-K batch run and watch live SSE telemetry.
        </p>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 space-y-4 max-w-lg">
          <label className="block text-sm">
            <span className="text-zinc-400">Tickers (comma-separated)</span>
            <input
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2"
              value={tickers}
              onChange={(e) => setTickers(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-zinc-400">Years</span>
            <input
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2"
              value={years}
              onChange={(e) => setYears(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-zinc-400">HITL mode</span>
            <select
              className="mt-1 w-full rounded-lg border border-zinc-700 bg-zinc-950 px-3 py-2"
              value={hitlMode}
              onChange={(e) => setHitlMode(e.target.value as typeof hitlMode)}
            >
              <option value="threshold_based">Threshold-based</option>
              <option value="review_all">Review all</option>
              <option value="auto_approve_all">Auto-approve all</option>
            </select>
          </label>
          {error && <p className="text-sm text-red-400">{error}</p>}
          <div className="flex gap-2">
          <button
            type="button"
            onClick={startRun}
            disabled={loading}
            className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
          >
            {loading ? "Starting…" : "Start batch run"}
          </button>
          <button
            type="button"
            disabled={hydrating}
            onClick={async () => {
              setHydrating(true);
              setError(null);
              try {
                await hydrateCache({
                  filing_types: ["10-K"],
                  tickers: tickers.split(",").map((t) => t.trim()).filter(Boolean),
                  years: years.split(",").map((y) => parseInt(y.trim(), 10)).filter((n) => !Number.isNaN(n)),
                });
              } catch (e) {
                setError(e instanceof Error ? e.message : "Hydrate failed");
              } finally {
                setHydrating(false);
              }
            }}
            className="rounded-lg border border-zinc-600 px-4 py-2 text-sm hover:border-zinc-400 disabled:opacity-50"
          >
            {hydrating ? "Hydrating…" : "Hydrate cache"}
          </button>
          </div>
        </div>
      </main>
    </div>
  );
}
