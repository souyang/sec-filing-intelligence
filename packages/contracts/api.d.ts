/**
 * Auto-generated from FastAPI OpenAPI spec.
 * Regenerate: pnpm generate:contracts (requires API running on :8000)
 */
export interface paths {
  "/health": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              status: string;
            };
          };
        };
      };
    };
  };
  "/api/runs": {
    post: {
      requestBody: {
        content: {
          "application/json": components["schemas"]["CreateBatchRunRequest"];
        };
      };
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["CreateBatchRunResponse"];
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    CreateBatchRunRequest: {
      profile: RunProfile;
    };
    CreateBatchRunResponse: {
      run_id: string;
      temporal_workflow_id: string;
      status: string;
    };
    RunProfile: {
      filing_types?: string[];
      tickers?: string[];
      years?: number[];
      hitl_mode?: "auto_approve_all" | "review_all" | "threshold_based";
    };
  };
}

export type RunProfile = components["schemas"]["RunProfile"];
