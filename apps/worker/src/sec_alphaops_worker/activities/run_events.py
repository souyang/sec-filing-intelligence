from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass
from typing import Any

from sec_alphaops_common.events.sse import FilingStageEvent, RunCounterEvent, RunStatusEvent
from sec_alphaops_common.infra.events import RunEventPublisher
from sec_alphaops_db.repositories import AuditRepository, RunRepository
from sec_alphaops_db.session import get_async_session_factory
from temporalio import activity

from sec_alphaops_worker.settings import settings


def _to_dict(input: object) -> dict[str, Any]:
    if is_dataclass(input) and not isinstance(input, type):
        return asdict(input)
    if isinstance(input, dict):
        return input
    return {}


@activity.defn(name="PublishRunEventActivity")
async def publish_run_event(input: dict[str, Any]) -> dict[str, str]:
    payload = _to_dict(input)
    run_id = payload["run_id"]
    event_payload = payload.get("event", payload)
    publisher = RunEventPublisher(settings.redis_url)
    entry_id = await publisher.publish(run_id, event_payload)

    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        await AuditRepository(session).log(
            uuid.UUID(str(run_id)),
            event_payload.get("type", "event"),
            event_payload,
            filing_id=uuid.UUID(payload["filing_id"]) if payload.get("filing_id") else None,
        )
    return {"entry_id": entry_id}


@activity.defn(name="UpdateRunCountersActivity")
async def update_run_counters(input: dict[str, Any]) -> dict[str, int]:
    payload = _to_dict(input)
    run_id = uuid.UUID(str(payload["run_id"]))
    factory = get_async_session_factory(settings.database_url)

    async with factory() as session:
        repo = RunRepository(session)
        if payload.get("increment"):
            run = await repo.increment_completed(run_id, failed=payload.get("failed", False))
        else:
            await repo.update_counters(
                run_id,
                completed=payload.get("completed"),
                failed=payload.get("failed"),
                review_pending=payload.get("review_pending"),
                status=payload.get("status"),
            )
            run = await repo.get(run_id)
            if not run:
                return {}
        counters = {
            "completed": run.completed_filings,
            "failed": run.failed_filings,
            "review_pending": run.review_pending,
            "in_progress": max(
                0,
                run.total_filings - run.completed_filings - run.failed_filings - run.review_pending,
            ),
        }

    event = RunCounterEvent(run_id=run_id, **counters)
    publisher = RunEventPublisher(settings.redis_url)
    await publisher.publish(run_id, event.model_dump(mode="json"))
    return counters


@activity.defn(name="EmitFilingStageActivity")
async def emit_filing_stage(input: dict[str, Any]) -> None:
    payload = _to_dict(input)
    run_id = uuid.UUID(str(payload["run_id"]))
    filing_id = uuid.UUID(str(payload["filing_id"]))
    event = FilingStageEvent(
        run_id=run_id,
        filing_id=filing_id,
        ticker=payload["ticker"],
        stage=payload["stage"],
        status=payload["status"],
        message=payload.get("message"),
    )
    publisher = RunEventPublisher(settings.redis_url)
    await publisher.publish(run_id, event.model_dump(mode="json"))

    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        from sec_alphaops_db.repositories import FilingRepository

        await FilingRepository(session).update_stage(
            filing_id, payload["status"], payload["stage"]
        )


@activity.defn(name="SetRunStatusActivity")
async def set_run_status(input: dict[str, Any]) -> None:
    payload = _to_dict(input)
    run_id = uuid.UUID(str(payload["run_id"]))
    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        await RunRepository(session).update_counters(
            run_id, status=payload.get("status", "running")
        )
    event = RunStatusEvent(
        run_id=run_id,
        status=payload.get("status", "running"),
        message=payload.get("message"),
    )
    await RunEventPublisher(settings.redis_url).publish(run_id, event.model_dump(mode="json"))
