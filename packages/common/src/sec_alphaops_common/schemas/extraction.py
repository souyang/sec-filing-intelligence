from __future__ import annotations

from pydantic import BaseModel, Field


class Citation(BaseModel):
    section: str
    excerpt: str
    page_hint: str | None = None


class RiskFactor(BaseModel):
    title: str
    summary: str
    severity: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class KPIData(BaseModel):
    metric: str
    value: str
    period: str | None = None
    unit: str | None = None
    citations: list[Citation] = Field(default_factory=list)


class ExtractionResult(BaseModel):
    """Base extraction contract shared across filing types."""

    filing_type: str
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = ""
    citations: list[Citation] = Field(default_factory=list)
    provenance_ids: list[str] = Field(default_factory=list)
    policy_flags: list[str] = Field(default_factory=list)


class TenKExtractionResult(ExtractionResult):
    filing_type: str = "10-K"
    risk_factors: list[RiskFactor] = Field(default_factory=list)
    kpi_data: list[KPIData] = Field(default_factory=list)
    segment_breakdown: dict[str, str] = Field(default_factory=dict)
