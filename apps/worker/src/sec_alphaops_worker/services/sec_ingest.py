from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any

from sec_alphaops_common.infra.r2 import R2Client


def configure_edgar() -> None:
    identity = os.environ.get("SEC_EDGAR_IDENTITY", "SEC AlphaOps dev@example.com")
    try:
        from edgar import set_identity

        set_identity(identity)
    except Exception:
        pass


def _local_edgar_dir() -> Path:
    return Path.home() / ".edgar"


async def download_filings(
    tickers: list[str],
    years: list[int],
    filing_types: list[str],
) -> dict[str, int]:
    configure_edgar()
    downloaded = 0
    skipped = 0

    try:
        from edgar import get_filings
    except ImportError:
        return {"downloaded": 0, "skipped": 0, "error": "edgartools not available"}

    for ticker in tickers:
        for year in years:
            for form in filing_types:
                try:
                    filings = get_filings(year=year, form=form, ticker=ticker)
                    for filing in filings:
                        try:
                            filing.download()
                            downloaded += 1
                        except Exception:
                            skipped += 1
                except Exception:
                    skipped += 1
    return {"downloaded": downloaded, "skipped": skipped}


async def sync_to_r2(
    tickers: list[str],
    years: list[int],
    filing_types: list[str],
    r2: R2Client,
) -> dict[str, int]:
    synced = 0
    skipped = 0
    cache_dir = _local_edgar_dir()
    if not cache_dir.exists():
        return {"synced": 0, "skipped": 0}

    for ticker in tickers:
        for year in years:
            for form in filing_types:
                for path in cache_dir.rglob("*.txt"):
                    if ticker.upper() not in path.name.upper():
                        continue
                    accession = path.stem
                    key = r2.cache_key(form, ticker, year, accession)
                    if r2.exists(key):
                        skipped += 1
                        continue
                    r2.put_text(key, path.read_text(encoding="utf-8", errors="replace"))
                    synced += 1
    return {"synced": synced, "skipped": skipped}


async def fetch_filing_text(
    ticker: str,
    year: int,
    filing_type: str,
    r2: R2Client | None,
) -> dict[str, Any]:
    configure_edgar()
    accession = f"{ticker}-{year}-{filing_type}".replace(" ", "")

    if r2:
        key = r2.cache_key(filing_type, ticker, year, accession)
        text = r2.get_text(key)
        if text:
            return {
                "text": text,
                "source": "r2",
                "ticker": ticker,
                "accession": accession,
                "object_key": key,
                "checksum": hashlib.sha256(text.encode()).hexdigest(),
            }

    try:
        from edgar import use_local_storage

        use_local_storage()
        from edgar import get_filings

        filings = get_filings(year=year, form=filing_type, ticker=ticker)
        for filing in filings:
            try:
                text = filing.text() if hasattr(filing, "text") else str(filing)
                if text:
                    return {
                        "text": text,
                        "source": "local_edgar",
                        "ticker": ticker,
                        "accession": getattr(filing, "accession_number", accession),
                        "checksum": hashlib.sha256(text.encode()).hexdigest(),
                    }
            except Exception:
                continue
    except Exception:
        pass

    # Demo fallback for dev without filings
    demo = (
        f"Item 1A. Risk Factors — {ticker} may face market, regulatory, and operational risks.\n"
        f"Item 7. MD&A — Revenue grew year-over-year in {year}.\n"
        f"Item 8. Financial Statements — Net income $1.2B; revenue $10.5B.\n"
    )
    return {
        "text": demo,
        "source": "demo",
        "ticker": ticker,
        "accession": accession,
        "checksum": hashlib.sha256(demo.encode()).hexdigest(),
    }


def parse_chunks(text: str, filing_type: str) -> list[dict]:
    if not text:
        return [{"chunk_id": "0", "text": "", "section": None, "metadata": {}}]

    chunks: list[dict] = []
    parts = []
    for label in ("Item 1A", "Item 7", "Item 8"):
        idx = text.find(label)
        if idx >= 0:
            parts.append((label, idx))
    parts.sort(key=lambda x: x[1])

    if not parts:
        size = 4000
        for i in range(0, len(text), size):
            chunks.append(
                {
                    "chunk_id": str(len(chunks)),
                    "text": text[i : i + size],
                    "section": None,
                    "metadata": {"filing_type": filing_type},
                }
            )
        return chunks or [{"chunk_id": "0", "text": text[:8000], "section": None, "metadata": {}}]

    for i, (label, start) in enumerate(parts):
        end = parts[i + 1][1] if i + 1 < len(parts) else len(text)
        segment = text[start:end]
        chunks.append(
            {
                "chunk_id": str(len(chunks)),
                "text": segment,
                "section": label,
                "metadata": {"filing_type": filing_type},
            }
        )
    return chunks
