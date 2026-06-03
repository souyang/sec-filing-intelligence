from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class ReviewTaskSummary(BaseModel):
    id: UUID
    run_id: UUID
    filing_id: UUID
    temporal_workflow_id: str
    status: str
    confidence: float | None
    payload: dict = Field(default_factory=dict)
    ticker: str | None = None
    created_at: datetime


class ReviewDecisionRequest(BaseModel):
    action: Literal["approve", "edit_approve", "reject"]
    note: str | None = None
    edited_analysis: dict | None = None


class ReviewDecisionResponse(BaseModel):
    task_id: UUID
    workflow_id: str
    result: str
