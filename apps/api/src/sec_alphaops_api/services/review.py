from __future__ import annotations

import uuid

from sec_alphaops_common.infra.temporal_client import (
    execute_update,
    get_temporal_client_from_settings,
)
from sec_alphaops_common.schemas.review import (
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewTaskSummary,
)
from sec_alphaops_db.models import Filing
from sec_alphaops_db.repositories import ReviewRepository, RunRepository
from sec_alphaops_workflows.human_review import ReviewDecision
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.settings import settings


class ReviewService:
    def __init__(self, session: AsyncSession) -> None:
        self._reviews = ReviewRepository(session)
        self._session = session

    async def list_pending(self) -> list[ReviewTaskSummary]:
        tasks = await self._reviews.list_pending()
        summaries = []
        for task in tasks:
            ticker = None
            result = await self._session.execute(
                select(Filing.ticker).where(Filing.id == task.filing_id)
            )
            row = result.scalar_one_or_none()
            if row:
                ticker = row
            summaries.append(
                ReviewTaskSummary(
                    id=task.id,
                    run_id=task.run_id,
                    filing_id=task.filing_id,
                    temporal_workflow_id=task.temporal_workflow_id,
                    status=task.status,
                    confidence=task.confidence,
                    payload=task.payload,
                    ticker=ticker,
                    created_at=task.created_at,
                )
            )
        return summaries

    async def submit_decision(
        self, task_id: uuid.UUID, body: ReviewDecisionRequest
    ) -> ReviewDecisionResponse:
        task = await self._reviews.get(task_id)
        if not task:
            raise ValueError(f"Review task {task_id} not found")
        if task.status != "pending":
            raise ValueError("Task already resolved")

        decision = ReviewDecision(
            action=body.action,
            edited_analysis=body.edited_analysis,
            note=body.note,
        )
        client = await get_temporal_client_from_settings(settings)
        result = await execute_update(
            client,
            task.temporal_workflow_id,
            "submit_review",
            decision,
        )

        await self._reviews.resolve(task_id, body.action, body.note)

        runs = RunRepository(self._session)
        run = await runs.get(task.run_id)
        if run and run.review_pending > 0:
            run.review_pending -= 1
            await self._session.commit()

        return ReviewDecisionResponse(
            task_id=task_id,
            workflow_id=task.temporal_workflow_id,
            result=str(result),
        )
