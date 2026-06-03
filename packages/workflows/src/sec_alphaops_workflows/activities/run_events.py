from __future__ import annotations

from typing import Any

from temporalio import activity


@activity.defn(name="PublishRunEventActivity")
async def PublishRunEventActivity(input: dict[str, Any]) -> dict[str, str]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="UpdateRunCountersActivity")
async def UpdateRunCountersActivity(input: dict[str, Any]) -> dict[str, int]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="EmitFilingStageActivity")
async def EmitFilingStageActivity(input: dict[str, Any]) -> None:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="SetRunStatusActivity")
async def SetRunStatusActivity(input: dict[str, Any]) -> None:
    raise NotImplementedError("Run in apps/worker")
