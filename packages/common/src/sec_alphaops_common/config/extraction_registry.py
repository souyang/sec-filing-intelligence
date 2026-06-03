from __future__ import annotations

from pydantic import BaseModel

from sec_alphaops_common.schemas.extraction import ExtractionResult, TenKExtractionResult


class ExtractionSchemaRegistry:
    """Maps filing types to Pydantic output models."""

    _SCHEMAS: dict[str, type[BaseModel]] = {
        "10-K": TenKExtractionResult,
    }

    @classmethod
    def get(cls, filing_type: str) -> type[BaseModel]:
        schema = cls._SCHEMAS.get(filing_type)
        if schema is None:
            supported = ", ".join(sorted(cls._SCHEMAS))
            raise KeyError(f"No extraction schema for {filing_type!r}. Supported: {supported}")
        return schema

    @classmethod
    def base(cls) -> type[ExtractionResult]:
        return ExtractionResult
