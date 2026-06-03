from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from sec_alphaops_common.infra.r2 import R2Client
from temporalio import activity

from sec_alphaops_worker.services.sec_ingest import download_filings, sync_to_r2


def _to_dict(input: object) -> dict[str, Any]:
    if is_dataclass(input) and not isinstance(input, type):
        return asdict(input)
    if isinstance(input, dict):
        return input
    return {}


@activity.defn(name="BulkDownloadActivity")
async def bulk_download(input: dict[str, Any]) -> dict[str, int]:
    payload = _to_dict(input)
    tickers = payload.get("tickers", [])
    years = payload.get("years", [])
    filing_types = payload.get("filing_types", ["10-K"])
    result = await download_filings(tickers, years, filing_types)
    activity.logger.info("BulkDownloadActivity", extra=result)
    return result


@activity.defn(name="SyncCacheToR2Activity")
async def sync_cache_to_r2(input: dict[str, Any]) -> dict[str, int]:
    payload = _to_dict(input)
    r2 = R2Client.from_env()
    if r2 is None:
        activity.logger.warning("R2 not configured; skipping sync")
        return {"synced": 0, "skipped": 0}
    return await sync_to_r2(
        payload.get("tickers", []),
        payload.get("years", []),
        payload.get("filing_types", ["10-K"]),
        r2,
    )
