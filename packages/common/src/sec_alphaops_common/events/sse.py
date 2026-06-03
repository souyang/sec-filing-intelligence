from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class SSEEventType(StrEnum):
    RUN_COUNTERS = "run.counters"
    FILING_STAGE = "filing.stage"
    RUN_STATUS = "run.status"
    WORKER_METRIC = "worker.metric"


class RunCounterEvent(BaseModel):
    type: Literal[SSEEventType.RUN_COUNTERS] = SSEEventType.RUN_COUNTERS
    run_id: UUID
    completed: int = 0
    failed: int = 0
    review_pending: int = 0
    in_progress: int = 0


class FilingStageEvent(BaseModel):
    type: Literal[SSEEventType.FILING_STAGE] = SSEEventType.FILING_STAGE
    run_id: UUID
    filing_id: UUID
    ticker: str
    stage: str
    status: str
    message: str | None = None


class RunStatusEvent(BaseModel):
    type: Literal[SSEEventType.RUN_STATUS] = SSEEventType.RUN_STATUS
    run_id: UUID
    status: str
    message: str | None = None


class WorkerMetricEvent(BaseModel):
    type: Literal[SSEEventType.WORKER_METRIC] = SSEEventType.WORKER_METRIC
    run_id: UUID
    metric: str
    value: float
    unit: str | None = None


SSEEvent = Annotated[
    RunCounterEvent | FilingStageEvent | RunStatusEvent | WorkerMetricEvent,
    Field(discriminator="type"),
]


def export_sse_json_schema() -> dict:
    """Export union JSON Schema for cross-language contract generation."""
    from pydantic import TypeAdapter

    adapter = TypeAdapter(SSEEvent)
    return adapter.json_schema()
