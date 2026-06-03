from __future__ import annotations

import json
from typing import Any
from uuid import UUID

import redis.asyncio as redis

STREAM_MAXLEN = 10_000


class RunEventPublisher:
    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url

    def _stream_key(self, run_id: str | UUID) -> str:
        return f"run:{run_id}:events"

    async def publish(self, run_id: str | UUID, payload: dict[str, Any]) -> str:
        client = redis.from_url(self._redis_url, decode_responses=True)
        try:
            entry_id = await client.xadd(
                self._stream_key(run_id),
                {"data": json.dumps(payload)},
                maxlen=STREAM_MAXLEN,
                approximate=True,
            )
            return str(entry_id)
        finally:
            await client.aclose()
