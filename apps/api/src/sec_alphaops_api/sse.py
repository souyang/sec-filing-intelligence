from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import redis.asyncio as redis

from sec_alphaops_api.settings import settings


async def stream_run_events(
    run_id: str,
    last_event_id: str | None,
) -> AsyncIterator[tuple[str, dict]]:
    """Read Redis Stream run:{runId}:events via XREAD; yield (entry_id, payload)."""
    stream_key = f"run:{run_id}:events"
    cursor = last_event_id or "0-0"
    client = redis.from_url(settings.redis_url, decode_responses=True)

    try:
        while True:
            entries = await client.xread({stream_key: cursor}, block=5000, count=50)
            if not entries:
                await asyncio.sleep(0.1)
                continue
            for _stream, messages in entries:
                for entry_id, fields in messages:
                    cursor = entry_id
                    raw = fields.get("data") or fields.get("payload") or "{}"
                    payload = json.loads(raw) if isinstance(raw, str) else raw
                    yield entry_id, payload
    finally:
        await client.aclose()
