from __future__ import annotations

import hashlib
import json
from typing import Any

from sec_alphaops_common.config.filing_registry import FilingTypeProfile
from sec_alphaops_common.config.prompt_store import PromptTemplateStore

from sec_alphaops_langgraph.nodes import NODE_FUNCS, GraphState


class LangGraphBuilder:
    """Runs filing-type node pipeline (linear topology from profile)."""

    def __init__(self, prompt_store: PromptTemplateStore | None = None) -> None:
        self._prompts = prompt_store or PromptTemplateStore()

    def cache_key(self, node_name: str, state: GraphState, profile: FilingTypeProfile) -> str:
        payload = {
            "node": node_name,
            "chunks": [c.get("text", "")[:500] for c in state.get("chunks", [])],
            "prompt_version": state.get("prompt_version"),
            "model": profile.model_tiers.get(node_name),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

    def build(self, profile: FilingTypeProfile, prompt_version: str | None = None) -> dict[str, Any]:
        return {
            "nodes": list(profile.node_names),
            "profile": profile,
            "prompt_version": prompt_version,
        }

    async def run(
        self,
        graph: dict[str, Any],
        chunks: list[dict],
        profile: FilingTypeProfile,
        *,
        ticker: str = "",
        cache: dict[str, dict] | None = None,
    ) -> dict[str, Any]:
        cache = cache or {}
        state: GraphState = {
            "ticker": ticker,
            "filing_type": profile.filing_type,
            "chunks": chunks,
            "prompt_version": graph.get("prompt_version"),
            "risk_factors": [],
            "kpi_data": [],
            "citations": [],
            "provenance_ids": [],
            "policy_flags": [],
            "confidence": 0.0,
            "rationale": "",
        }

        for node_name in profile.node_names:
            key = self.cache_key(node_name, state, profile)
            if key in cache:
                state.update(cache[key])  # type: ignore[typeddict-item]
                continue
            fn = NODE_FUNCS.get(node_name)
            if fn is None:
                continue
            result = await fn(state, profile, self._prompts)
            cache[key] = result
            state.update(result)  # type: ignore[typeddict-item]

        return {
            "filing_type": profile.filing_type,
            "confidence": state.get("confidence", 0.0),
            "rationale": state.get("rationale", ""),
            "citations": state.get("citations", []),
            "provenance_ids": state.get("provenance_ids", []),
            "policy_flags": state.get("policy_flags", []),
            "risk_factors": state.get("risk_factors", []),
            "kpi_data": state.get("kpi_data", []),
        }
