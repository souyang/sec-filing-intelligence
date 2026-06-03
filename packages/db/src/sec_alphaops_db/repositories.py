from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from sec_alphaops_common.config.run_profile import RunProfile
from sec_alphaops_common.schemas.run import WorkflowRunStatus, WorkflowRunSummary
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from sec_alphaops_db.models import Chunk, EventAudit, Extraction, Filing, ReviewTask, WorkflowRun


class RunRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        run_id: uuid.UUID,
        temporal_workflow_id: str,
        profile: RunProfile,
        total_filings: int,
    ) -> WorkflowRun:
        row = WorkflowRun(
            id=run_id,
            temporal_workflow_id=temporal_workflow_id,
            status=WorkflowRunStatus.PENDING.value,
            profile=profile.model_dump(),
            total_filings=total_filings,
        )
        self._session.add(row)
        await self._session.commit()
        await self._session.refresh(row)
        return row

    async def get(self, run_id: uuid.UUID) -> WorkflowRun | None:
        return await self._session.get(WorkflowRun, run_id)

    async def update_counters(
        self,
        run_id: uuid.UUID,
        *,
        completed: int | None = None,
        failed: int | None = None,
        review_pending: int | None = None,
        status: str | None = None,
    ) -> None:
        values: dict[str, Any] = {"updated_at": datetime.now(UTC)}
        if completed is not None:
            values["completed_filings"] = completed
        if failed is not None:
            values["failed_filings"] = failed
        if review_pending is not None:
            values["review_pending"] = review_pending
        if status is not None:
            values["status"] = status
        await self._session.execute(
            update(WorkflowRun).where(WorkflowRun.id == run_id).values(**values)
        )
        await self._session.commit()

    async def increment_completed(self, run_id: uuid.UUID, failed: bool = False) -> WorkflowRun:
        run = await self.get(run_id)
        if not run:
            raise ValueError(f"Run {run_id} not found")
        if failed:
            run.failed_filings += 1
        else:
            run.completed_filings += 1
        if run.completed_filings + run.failed_filings >= run.total_filings:
            run.status = WorkflowRunStatus.COMPLETED.value
        run.updated_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(run)
        return run

    def to_summary(self, row: WorkflowRun) -> WorkflowRunSummary:
        return WorkflowRunSummary(
            id=row.id,
            status=WorkflowRunStatus(row.status),
            profile=RunProfile.model_validate(row.profile),
            total_filings=row.total_filings,
            completed_filings=row.completed_filings,
            failed_filings=row.failed_filings,
            review_pending=row.review_pending,
            created_at=row.created_at,
            updated_at=row.updated_at,
        )


class FilingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        run_id: uuid.UUID,
        ticker: str,
        year: int,
        filing_type: str,
        **kwargs: Any,
    ) -> Filing:
        stmt = (
            insert(Filing)
            .values(
                id=kwargs.get("id", uuid.uuid4()),
                run_id=run_id,
                ticker=ticker.upper(),
                year=year,
                filing_type=filing_type,
                accession=kwargs.get("accession"),
                object_key=kwargs.get("object_key"),
                status=kwargs.get("status", "queued"),
                stage=kwargs.get("stage"),
            )
            .on_conflict_do_update(
                constraint="uq_filing_per_run",
                set_={
                    "status": kwargs.get("status", "queued"),
                    "stage": kwargs.get("stage"),
                    "object_key": kwargs.get("object_key"),
                    "accession": kwargs.get("accession"),
                    "updated_at": datetime.now(UTC),
                },
            )
            .returning(Filing)
        )
        result = await self._session.execute(stmt)
        await self._session.commit()
        return result.scalar_one()

    async def update_stage(
        self, filing_id: uuid.UUID, status: str, stage: str, error: str | None = None
    ) -> None:
        await self._session.execute(
            update(Filing)
            .where(Filing.id == filing_id)
            .values(status=status, stage=stage, error_message=error, updated_at=datetime.now(UTC))
        )
        await self._session.commit()

    async def get_by_run(self, run_id: uuid.UUID) -> list[Filing]:
        result = await self._session.execute(select(Filing).where(Filing.run_id == run_id))
        return list(result.scalars().all())


class ReviewRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        run_id: uuid.UUID,
        filing_id: uuid.UUID,
        temporal_workflow_id: str,
        confidence: float,
        payload: dict,
    ) -> ReviewTask:
        task = ReviewTask(
            run_id=run_id,
            filing_id=filing_id,
            temporal_workflow_id=temporal_workflow_id,
            confidence=confidence,
            payload=payload,
            status="pending",
        )
        self._session.add(task)
        await self._session.commit()
        await self._session.refresh(task)
        return task

    async def list_pending(self) -> list[ReviewTask]:
        result = await self._session.execute(
            select(ReviewTask).where(ReviewTask.status == "pending").order_by(ReviewTask.created_at)
        )
        return list(result.scalars().all())

    async def get(self, task_id: uuid.UUID) -> ReviewTask | None:
        return await self._session.get(ReviewTask, task_id)

    async def resolve(
        self, task_id: uuid.UUID, decision: str, note: str | None = None
    ) -> ReviewTask:
        task = await self.get(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        task.status = "resolved"
        task.decision = decision
        task.reviewer_note = note
        task.resolved_at = datetime.now(UTC)
        await self._session.commit()
        await self._session.refresh(task)
        return task


class ExtractionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        filing_id: uuid.UUID,
        run_id: uuid.UUID,
        filing_type: str,
        payload: dict,
        confidence: float,
        review_status: str = "auto",
    ) -> None:
        stmt = (
            insert(Extraction)
            .values(
                id=uuid.uuid4(),
                filing_id=filing_id,
                run_id=run_id,
                filing_type=filing_type,
                payload=payload,
                confidence=confidence,
                review_status=review_status,
            )
            .on_conflict_do_update(
                constraint="uq_extraction_per_filing",
                set_={
                    "payload": payload,
                    "confidence": confidence,
                    "review_status": review_status,
                },
            )
        )
        await self._session.execute(stmt)
        await self._session.commit()


class ChunkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def replace_for_filing(self, filing_id: uuid.UUID, chunks: list[dict]) -> None:
        from sqlalchemy import delete

        await self._session.execute(delete(Chunk).where(Chunk.filing_id == filing_id))
        for i, c in enumerate(chunks):
            self._session.add(
                Chunk(
                    filing_id=filing_id,
                    chunk_index=i,
                    section=c.get("section"),
                    text=c.get("text", ""),
                    chunk_metadata=c.get("metadata", {}),
                )
            )
        await self._session.commit()


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        run_id: uuid.UUID,
        event_type: str,
        payload: dict,
        filing_id: uuid.UUID | None = None,
    ) -> None:
        self._session.add(
            EventAudit(run_id=run_id, filing_id=filing_id, event_type=event_type, payload=payload)
        )
        await self._session.commit()
