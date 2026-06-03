from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from sec_alphaops_common.config.run_profile import RunProfile


class WorkflowRunStatus(StrEnum):
    PENDING = "pending"
    HYDRATING = "hydrating"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class WorkflowRunSummary(BaseModel):
    id: UUID
    status: WorkflowRunStatus
    profile: RunProfile
    total_filings: int = 0
    completed_filings: int = 0
    failed_filings: int = 0
    review_pending: int = 0
    created_at: datetime
    updated_at: datetime


class CreateBatchRunRequest(BaseModel):
    profile: RunProfile


class CreateBatchRunResponse(BaseModel):
    run_id: UUID
    temporal_workflow_id: str
    status: WorkflowRunStatus = WorkflowRunStatus.PENDING
