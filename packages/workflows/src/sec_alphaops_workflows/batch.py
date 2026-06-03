from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from sec_alphaops_common.config.run_profile import RunProfile

    from sec_alphaops_workflows.activities.run_events import (
        SetRunStatusActivity,
        UpdateRunCountersActivity,
    )
    from sec_alphaops_workflows.filing import FilingProcessingInput, FilingProcessingWorkflow


@dataclass
class BatchOrchestratorInput:
    run_id: str
    profile: dict[str, Any]


@workflow.defn(name="BatchOrchestratorWorkflow")
class BatchOrchestratorWorkflow:
    @workflow.run
    async def run(self, input: BatchOrchestratorInput) -> dict[str, int]:
        profile = RunProfile.model_validate(input.profile)
        retry = RetryPolicy(maximum_attempts=3)

        await workflow.execute_activity(
            SetRunStatusActivity,
            {"run_id": input.run_id, "status": "running", "message": "Batch started"},
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        child_handles = []
        for ticker in profile.tickers:
            for year in profile.years:
                for filing_type in profile.filing_types:
                    child_id = f"{input.run_id}-{ticker}-{year}-{filing_type}"
                    handle = await workflow.start_child_workflow(
                        FilingProcessingWorkflow.run,
                        FilingProcessingInput(
                            run_id=input.run_id,
                            ticker=ticker,
                            year=year,
                            filing_type=filing_type,
                            profile=profile.model_dump(),
                        ),
                        id=child_id,
                        task_queue=workflow.info().task_queue,
                        retry_policy=retry,
                    )
                    child_handles.append(handle)

        completed = 0
        failed = 0
        for handle in child_handles:
            try:
                await handle
                completed += 1
            except Exception:
                failed += 1
                await workflow.execute_activity(
                    UpdateRunCountersActivity,
                    {"run_id": input.run_id, "increment": True, "failed": True},
                    start_to_close_timeout=timedelta(minutes=2),
                    retry_policy=retry,
                )

        await workflow.execute_activity(
            SetRunStatusActivity,
            {
                "run_id": input.run_id,
                "status": "completed",
                "message": f"Batch finished: {completed} ok, {failed} failed",
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        return {"completed": completed, "failed": failed, "total": len(child_handles)}
