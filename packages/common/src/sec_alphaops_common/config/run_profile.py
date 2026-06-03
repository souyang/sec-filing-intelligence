from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class RunProfile(BaseModel):
    """First-class input for BatchOrchestratorWorkflow."""

    filing_types: list[str] = Field(default_factory=lambda: ["10-K"])
    tickers: list[str] = Field(default_factory=list)
    years: list[int] = Field(default_factory=list)
    model_overrides: dict[str, str] = Field(default_factory=dict)
    confidence_thresholds: dict[str, float] = Field(default_factory=dict)
    hitl_mode: Literal["auto_approve_all", "review_all", "threshold_based"] = "threshold_based"
    prompt_version: str | None = None
    max_parallel_filings: int = Field(default=10, ge=1, le=100)
    failure_budget_pct: float = Field(default=10.0, ge=0.0, le=100.0)
