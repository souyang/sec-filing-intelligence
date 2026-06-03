import pytest
from sec_alphaops_common.config.filing_registry import FilingTypeRegistry
from sec_alphaops_common.config.run_profile import RunProfile


def test_filing_type_registry_10k() -> None:
    profile = FilingTypeRegistry.get("10-K")
    assert profile.filing_type == "10-K"
    assert "sectionClassifier" in profile.node_names
    assert len(profile.edge_pairs) == 5


def test_unknown_filing_type_raises() -> None:
    with pytest.raises(KeyError, match="Unknown filing type"):
        FilingTypeRegistry.get("DEF-14A")


def test_run_profile_defaults() -> None:
    profile = RunProfile(tickers=["AAPL"], years=[2023])
    assert profile.filing_types == ["10-K"]
    assert profile.hitl_mode == "threshold_based"
