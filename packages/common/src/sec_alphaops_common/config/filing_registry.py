from __future__ import annotations

from dataclasses import dataclass

from sec_alphaops_common.schemas.extraction import TenKExtractionResult


@dataclass(frozen=True)
class FilingTypeProfile:
    """Declarative config profile for a filing type."""

    filing_type: str
    sections: tuple[str, ...]
    node_names: tuple[str, ...]
    edge_pairs: tuple[tuple[str, str], ...]
    model_tiers: dict[str, str]
    confidence_threshold: float
    output_schema_name: str


class FilingTypeRegistry:
    """Code-only registry; profiles are not stored in Postgres."""

    _PROFILES: dict[str, FilingTypeProfile] = {
        "10-K": FilingTypeProfile(
            filing_type="10-K",
            sections=("Item 1A", "Item 7", "Item 8"),
            node_names=(
                "sectionClassifier",
                "riskExtractor",
                "kpiExtractor",
                "crossCheckNode",
                "confidenceScorer",
                "policyGuard",
            ),
            edge_pairs=(
                ("sectionClassifier", "riskExtractor"),
                ("riskExtractor", "kpiExtractor"),
                ("kpiExtractor", "crossCheckNode"),
                ("crossCheckNode", "confidenceScorer"),
                ("confidenceScorer", "policyGuard"),
            ),
            model_tiers={
                "sectionClassifier": "gpt-4.1-nano",
                "riskExtractor": "gpt-4.1-mini",
                "kpiExtractor": "gpt-4.1-mini",
                "crossCheckNode": "gpt-4.1",
                "confidenceScorer": "gpt-4.1-nano",
                "policyGuard": "gpt-4.1-nano",
            },
            confidence_threshold=0.75,
            output_schema_name=TenKExtractionResult.__name__,
        ),
    }

    @classmethod
    def get(cls, filing_type: str) -> FilingTypeProfile:
        profile = cls._PROFILES.get(filing_type)
        if profile is None:
            supported = ", ".join(sorted(cls._PROFILES))
            raise KeyError(f"Unknown filing type {filing_type!r}. Supported: {supported}")
        return profile

    @classmethod
    def list_types(cls) -> list[str]:
        return sorted(cls._PROFILES.keys())

    @classmethod
    def resolve_many(cls, filing_types: list[str]) -> dict[str, FilingTypeProfile]:
        return {ft: cls.get(ft) for ft in filing_types}
