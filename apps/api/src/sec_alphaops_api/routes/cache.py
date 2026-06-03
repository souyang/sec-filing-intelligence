from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sec_alphaops_common.schemas.run import CreateBatchRunRequest
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_api.deps import get_db
from sec_alphaops_api.services.runs import RunService

router = APIRouter(prefix="/api/cache", tags=["cache"])


@router.post("/hydrate")
async def hydrate_cache(
    body: CreateBatchRunRequest,
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if not body.profile.tickers or not body.profile.years:
        raise HTTPException(status_code=400, detail="tickers and years are required")
    workflow_id = await RunService(session).start_cache_hydrate(body.profile)
    return {"temporal_workflow_id": workflow_id, "status": "started"}
