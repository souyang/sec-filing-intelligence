from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from sec_alphaops_workflows.activities.cache import BulkDownloadActivity, SyncCacheToR2Activity


@dataclass
class CacheHydrateInput:
    tickers: list[str]
    years: list[int]
    filing_types: list[str]


@dataclass
class CacheHydrateResult:
    downloaded: int
    synced: int
    skipped: int


@workflow.defn(name="CacheHydrateWorkflow")
class CacheHydrateWorkflow:
    @workflow.run
    async def run(self, input: CacheHydrateInput) -> CacheHydrateResult:
        retry = RetryPolicy(
            initial_interval=timedelta(seconds=2),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )
        payload = {
            "tickers": input.tickers,
            "years": input.years,
            "filing_types": input.filing_types,
        }
        downloaded = await workflow.execute_activity(
            BulkDownloadActivity,
            payload,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry,
        )
        synced = await workflow.execute_activity(
            SyncCacheToR2Activity,
            payload,
            start_to_close_timeout=timedelta(hours=2),
            retry_policy=retry,
        )
        return CacheHydrateResult(
            downloaded=downloaded.get("downloaded", 0),
            synced=synced.get("synced", 0),
            skipped=synced.get("skipped", 0) + downloaded.get("skipped", 0),
        )
