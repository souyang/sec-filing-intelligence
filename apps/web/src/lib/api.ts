const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type RunProfile = {
  filing_types?: string[];
  tickers?: string[];
  years?: number[];
  hitl_mode?: "auto_approve_all" | "review_all" | "threshold_based";
  confidence_thresholds?: Record<string, number>;
};

export type CreateBatchRunResponse = {
  run_id: string;
  temporal_workflow_id: string;
  status: string;
};

export type WorkflowRunSummary = {
  id: string;
  status: string;
  profile: RunProfile;
  total_filings: number;
  completed_filings: number;
  failed_filings: number;
  review_pending: number;
  created_at: string;
  updated_at: string;
};

export type ReviewTask = {
  id: string;
  run_id: string;
  filing_id: string;
  temporal_workflow_id: string;
  status: string;
  confidence: number | null;
  payload: Record<string, unknown>;
  ticker: string | null;
  created_at: string;
};

export async function createBatchRun(profile: RunProfile): Promise<CreateBatchRunResponse> {
  const res = await fetch(`${API_BASE}/api/runs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile }),
  });
  if (!res.ok) throw new Error(`Failed to create run: ${res.status}`);
  return res.json() as Promise<CreateBatchRunResponse>;
}

export async function hydrateCache(profile: RunProfile): Promise<{ temporal_workflow_id: string }> {
  const res = await fetch(`${API_BASE}/api/cache/hydrate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ profile }),
  });
  if (!res.ok) throw new Error(`Hydrate failed: ${res.status}`);
  return res.json() as Promise<{ temporal_workflow_id: string }>;
}

export async function getRun(runId: string): Promise<WorkflowRunSummary> {
  const res = await fetch(`${API_BASE}/api/runs/${runId}`);
  if (!res.ok) throw new Error(`Failed to load run: ${res.status}`);
  return res.json() as Promise<WorkflowRunSummary>;
}

export async function listReviewTasks(): Promise<ReviewTask[]> {
  const res = await fetch(`${API_BASE}/api/review-tasks`);
  if (!res.ok) throw new Error(`Failed to load review tasks: ${res.status}`);
  return res.json() as Promise<ReviewTask[]>;
}

export async function submitReviewDecision(
  taskId: string,
  action: "approve" | "edit_approve" | "reject",
  note?: string,
  edited_analysis?: Record<string, unknown>,
): Promise<void> {
  const res = await fetch(`${API_BASE}/api/review-tasks/${taskId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, note, edited_analysis }),
  });
  if (!res.ok) throw new Error(`Decision failed: ${res.status}`);
}

export function sseRunUrl(runId: string): string {
  const base = process.env.NEXT_PUBLIC_SSE_URL ?? `${API_BASE}/sse`;
  return `${base}/runs/${runId}`;
}
