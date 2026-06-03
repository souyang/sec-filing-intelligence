from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sec_alphaops_common.schemas.review import (
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ReviewTaskSummary,
)
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.deps import get_db
from sec_alphaops_api.services.review import ReviewService

router = APIRouter(prefix="/api/review-tasks", tags=["review"])


@router.get("", response_model=list[ReviewTaskSummary])
async def list_review_tasks(
    session: AsyncSession = Depends(get_db),
) -> list[ReviewTaskSummary]:
    return await ReviewService(session).list_pending()


@router.post("/{task_id}/decision", response_model=ReviewDecisionResponse)
async def submit_review_decision(
    task_id: UUID,
    body: ReviewDecisionRequest,
    session: AsyncSession = Depends(get_db),
) -> ReviewDecisionResponse:
    try:
        return await ReviewService(session).submit_decision(task_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
