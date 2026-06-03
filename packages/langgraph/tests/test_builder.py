import pytest
from sec_alphaops_common.config.filing_registry import FilingTypeRegistry
from sec_alphaops_langgraph.builder import LangGraphBuilder


@pytest.mark.asyncio
async def test_builder_demo_run() -> None:
    profile = FilingTypeRegistry.get("10-K")
    builder = LangGraphBuilder()
    graph = builder.build(profile)
    chunks = [{"chunk_id": "0", "text": "Item 1A. Risk Factors — market risk.\nItem 8. revenue $10B"}]
    result = await builder.run(graph, chunks, profile, ticker="AAPL")
    assert result["filing_type"] == "10-K"
    assert "confidence" in result
