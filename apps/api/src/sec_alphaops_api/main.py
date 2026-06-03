from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import FastAPI, Header
from fastapi.middleware.cors import CORSMiddleware
from sec_alphaops_common.events.sse import export_sse_json_schema
from sec_alphaops_db import run_migrations
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from sec_alphaops_api.routes import cache, health, review, runs
from sec_alphaops_api.settings import settings
from sec_alphaops_api.sse import stream_run_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sec_alphaops_api")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    await run_migrations()
    logger.info("API ready (env=%s)", settings.app_env)
    yield


app = FastAPI(
    title="SEC AlphaOps API",
    version="0.1.0",
    description="Configurable SEC filing intelligence pipeline",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(runs.router)
app.include_router(cache.router)
app.include_router(review.router)


@app.get("/sse/runs/{run_id}", tags=["sse"])
async def sse_run_events(
    run_id: UUID,
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
) -> EventSourceResponse:
    async def event_generator() -> AsyncIterator[ServerSentEvent]:
        async for entry_id, payload in stream_run_events(str(run_id), last_event_id):
            yield ServerSentEvent(
                id=entry_id,
                event=payload.get("type", "message"),
                data=json.dumps(payload),
            )

    return EventSourceResponse(event_generator())


@app.get("/api/contracts/sse-schema", tags=["contracts"])
async def sse_schema() -> dict:
    return export_sse_json_schema()
