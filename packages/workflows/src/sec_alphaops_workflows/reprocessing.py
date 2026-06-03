from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from sec_alphaops_workflows.batch import BatchOrchestratorInput, BatchOrchestratorWorkflow


@dataclass
class ReprocessingInput:
    original_run_id: str
    new_run_id: str
    profile: dict[str, Any]


@workflow.defn(name="ReprocessingWorkflow")
class ReprocessingWorkflow:
    @workflow.run
    async def run(self, input: ReprocessingInput) -> dict[str, int]:
        return await workflow.execute_child_workflow(
            BatchOrchestratorWorkflow.run,
            BatchOrchestratorInput(run_id=input.new_run_id, profile=input.profile),
            id=f"reprocess-{input.new_run_id}",
        )
