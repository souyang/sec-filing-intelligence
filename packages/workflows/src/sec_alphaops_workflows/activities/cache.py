from __future__ import annotations

from typing import Any

from temporalio import activity


@activity.defn(name="BulkDownloadActivity")
async def BulkDownloadActivity(input: dict[str, Any]) -> dict[str, int]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="SyncCacheToR2Activity")
async def SyncCacheToR2Activity(input: dict[str, Any]) -> dict[str, int]:
    raise NotImplementedError("Run in apps/worker")
