from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sec_alphaops_common.schemas.run import (
    CreateBatchRunRequest,
    CreateBatchRunResponse,
    WorkflowRunSummary,
)
from sec_alphaops_db.repositories import FilingRepository, RunRepository
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.deps import get_db
from sec_alphaops_api.services.runs import RunService

router = APIRouter(prefix="/api/runs", tags=["runs"])


@router.post("", response_model=CreateBatchRunResponse)
async def create_run(
    body: CreateBatchRunRequest,
    session: AsyncSession = Depends(get_db),
) -> CreateBatchRunResponse:
    if not body.profile.tickers or not body.profile.years:
        raise HTTPException(status_code=400, detail="tickers and years are required")
    service = RunService(session)
    return await service.create_batch(body.profile)


@router.get("/{run_id}", response_model=WorkflowRunSummary)
async def get_run(run_id: UUID, session: AsyncSession = Depends(get_db)) -> WorkflowRunSummary:
    repo = RunRepository(session)
    row = await repo.get(run_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return repo.to_summary(row)


@router.get("/{run_id}/filings")
async def list_filings(run_id: UUID, session: AsyncSession = Depends(get_db)) -> list[dict]:
    filings = await FilingRepository(session).get_by_run(run_id)
    return [
        {
            "id": str(f.id),
            "ticker": f.ticker,
            "year": f.year,
            "filing_type": f.filing_type,
            "status": f.status,
            "stage": f.stage,
            "error_message": f.error_message,
        }
        for f in filings
    ]

