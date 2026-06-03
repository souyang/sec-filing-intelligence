"use client";

import { useEffect, useState } from "react";
import ReconnectingEventSource from "reconnecting-eventsource";

import { sseRunUrl } from "@/lib/api";

export type RunEvent = {
  type?: string;
  completed?: number;
  failed?: number;
  review_pending?: number;
  in_progress?: number;
  stage?: string;
  status?: string;
  message?: string;
};

export function useRunSse(runId: string | null) {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!runId) return;

    const url = sseRunUrl(runId);
    const source = new ReconnectingEventSource(url);

    source.onopen = () => setConnected(true);
    source.onerror = () => setConnected(false);

    source.onmessage = (ev) => {
      try {
        const payload = JSON.parse(ev.data) as RunEvent;
        setEvents((prev) => [...prev.slice(-99), payload]);
      } catch {
        // ignore malformed events in bootstrap
      }
    };

    return () => {
      source.close();
      setConnected(false);
    };
  }, [runId]);

  const latestCounters = [...events]
    .reverse()
    .find((e) => e.type === "run.counters" || e.completed !== undefined);

  return { events, connected, latestCounters };
}
