from __future__ import annotations

from typing import Any

from temporalio import activity


@activity.defn(name="EnsureFilingRecordActivity")
async def EnsureFilingRecordActivity(input: dict[str, Any]) -> dict[str, str]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="FetchFilingActivity")
async def FetchFilingActivity(input: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="ParseChunkActivity")
async def ParseChunkActivity(input: dict[str, Any]) -> list[dict]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="LangGraphAnalysisActivity")
async def LangGraphAnalysisActivity(input: dict[str, Any]) -> dict[str, Any]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="CreateReviewTaskActivity")
async def CreateReviewTaskActivity(input: dict[str, Any]) -> dict[str, str]:
    raise NotImplementedError("Run in apps/worker")


@activity.defn(name="PersistInsightsActivity")
async def PersistInsightsActivity(input: dict[str, Any]) -> dict[str, str]:
    raise NotImplementedError("Run in apps/worker")
