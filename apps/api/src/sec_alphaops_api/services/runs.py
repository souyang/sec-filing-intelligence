from __future__ import annotations

import uuid

from sec_alphaops_common.config.run_profile import RunProfile
from sec_alphaops_common.infra.temporal_client import (
    get_temporal_client_from_settings,
    start_workflow,
)
from sec_alphaops_common.schemas.run import CreateBatchRunResponse, WorkflowRunStatus
from sec_alphaops_db.repositories import RunRepository
from sec_alphaops_workflows.batch import BatchOrchestratorInput, BatchOrchestratorWorkflow
from sec_alphaops_workflows.cache_hydrate import CacheHydrateInput, CacheHydrateWorkflow
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.settings import settings


def _count_filings(profile: RunProfile) -> int:
    return len(profile.tickers) * len(profile.years) * len(profile.filing_types)


class RunService:
    def __init__(self, session: AsyncSession) -> None:
        self._runs = RunRepository(session)

    async def create_batch(self, profile: RunProfile) -> CreateBatchRunResponse:
        run_id = uuid.uuid4()
        workflow_id = f"batch-{run_id}"
        total = _count_filings(profile)

        await self._runs.create(run_id, workflow_id, profile, total)
        await self._runs.update_counters(run_id, status=WorkflowRunStatus.RUNNING.value)

        client = await get_temporal_client_from_settings(settings)
        await start_workflow(
            client,
            BatchOrchestratorWorkflow.run,
            BatchOrchestratorInput(run_id=str(run_id), profile=profile.model_dump()),
            workflow_id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )

        return CreateBatchRunResponse(
            run_id=run_id,
            temporal_workflow_id=workflow_id,
            status=WorkflowRunStatus.RUNNING,
        )

    async def start_cache_hydrate(self, profile: RunProfile) -> str:
        workflow_id = f"hydrate-{uuid.uuid4()}"
        client = await get_temporal_client_from_settings(settings)
        await start_workflow(
            client,
            CacheHydrateWorkflow.run,
            CacheHydrateInput(
                tickers=profile.tickers,
                years=profile.years,
                filing_types=profile.filing_types,
            ),
            workflow_id=workflow_id,
            task_queue=settings.temporal_task_queue,
        )
        return workflow_id
