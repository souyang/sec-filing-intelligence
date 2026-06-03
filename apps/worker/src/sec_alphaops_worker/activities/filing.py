from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass
from typing import Any

from sec_alphaops_common.config.filing_registry import FilingTypeRegistry
from sec_alphaops_common.config.run_profile import RunProfile
from sec_alphaops_common.infra.r2 import R2Client
from sec_alphaops_db.repositories import (
    ChunkRepository,
    ExtractionRepository,
    FilingRepository,
    ReviewRepository,
)
from sec_alphaops_db.session import get_async_session_factory
from sec_alphaops_langgraph.builder import LangGraphBuilder
from temporalio import activity

from sec_alphaops_worker.services.sec_ingest import fetch_filing_text, parse_chunks
from sec_alphaops_worker.settings import settings


def _to_dict(input: object) -> dict[str, Any]:
    if is_dataclass(input) and not isinstance(input, type):
        return asdict(input)
    if isinstance(input, dict):
        return input
    return {}


def _filing_input(data: dict) -> dict[str, Any]:
    if "input" in data and isinstance(data["input"], dict):
        inner = data["input"]
        if is_dataclass(data["input"]):
            return asdict(data["input"])
        return inner
    return data


@activity.defn(name="EnsureFilingRecordActivity")
async def ensure_filing_record(input: dict[str, Any]) -> dict[str, str]:
    data = _to_dict(input)
    fin = _filing_input(data) if "run_id" not in data else data
    run_id = uuid.UUID(str(fin["run_id"]))
    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        filing = await FilingRepository(session).upsert(
            run_id,
            fin["ticker"],
            fin["year"],
            fin["filing_type"],
            status="queued",
            stage="init",
        )
    return {"filing_id": str(filing.id)}


@activity.defn(name="FetchFilingActivity")
async def fetch_filing(input: dict[str, Any]) -> dict[str, Any]:
    data = _to_dict(input)
    fin = _filing_input(data)
    r2 = R2Client.from_env()
    raw = await fetch_filing_text(
        fin["ticker"],
        fin["year"],
        fin["filing_type"],
        r2,
    )
    raw["filing_id"] = fin.get("filing_id")
    return raw


@activity.defn(name="ParseChunkActivity")
async def parse_chunk(input: dict[str, Any]) -> list[dict]:
    payload = _to_dict(input)
    raw = payload.get("raw", {})
    fin = _filing_input(payload.get("input", payload))
    text = raw.get("text", "")
    chunks = parse_chunks(text, fin.get("filing_type", "10-K"))

    filing_id = fin.get("filing_id") or raw.get("filing_id")
    if filing_id:
        factory = get_async_session_factory(settings.database_url)
        async with factory() as session:
            await ChunkRepository(session).replace_for_filing(uuid.UUID(str(filing_id)), chunks)
    return chunks


@activity.defn(name="LangGraphAnalysisActivity")
async def langgraph_analysis(input: dict[str, Any]) -> dict[str, Any]:
    payload = _to_dict(input)
    fin = _filing_input(payload.get("input", {}))
    filing_type = fin.get("filing_type", "10-K")
    profile_data = fin.get("profile", {})
    run_profile = RunProfile.model_validate(profile_data)
    profile_cfg = FilingTypeRegistry.get(filing_type)

    builder = LangGraphBuilder()
    graph = builder.build(profile_cfg, run_profile.prompt_version)
    chunks = payload.get("chunks", [])
    return await builder.run(
        graph,
        chunks,
        profile_cfg,
        ticker=fin.get("ticker", ""),
    )


@activity.defn(name="CreateReviewTaskActivity")
async def create_review_task(input: dict[str, Any]) -> dict[str, str]:
    payload = _to_dict(input)
    fin = _filing_input(payload.get("input", {}))
    run_id = uuid.UUID(str(fin["run_id"]))
    filing_id = uuid.UUID(str(fin.get("filing_id") or payload.get("filing_id")))
    analysis = payload.get("analysis", {})
    workflow_id = payload["temporal_workflow_id"]
    confidence = float(analysis.get("confidence", 0))

    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        from sec_alphaops_db.repositories import RunRepository

        task = await ReviewRepository(session).create(
            run_id,
            filing_id,
            workflow_id,
            confidence,
            analysis,
        )
        run = await RunRepository(session).get(run_id)
        if run:
            run.review_pending += 1
            await session.commit()

    return {"task_id": str(task.id), "temporal_workflow_id": workflow_id}


@activity.defn(name="PersistInsightsActivity")
async def persist_insights(input: dict[str, Any]) -> dict[str, str]:
    payload = _to_dict(input)
    fin = _filing_input(payload.get("input", {}))
    analysis = payload.get("analysis", {})
    run_id = uuid.UUID(str(fin["run_id"]))
    filing_id = uuid.UUID(str(fin.get("filing_id") or payload.get("filing_id")))

    review_status = "reviewed" if analysis.get("status") in ("approved", "rejected") else "auto"
    factory = get_async_session_factory(settings.database_url)
    async with factory() as session:
        await ExtractionRepository(session).upsert(
            filing_id,
            run_id,
            fin.get("filing_type", "10-K"),
            analysis,
            float(analysis.get("confidence", 0)),
            review_status,
        )
        await FilingRepository(session).update_stage(
            filing_id, "completed", "persisted"
        )
    return {"status": "persisted", "filing_id": str(filing_id)}
