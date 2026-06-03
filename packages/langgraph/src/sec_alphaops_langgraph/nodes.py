from __future__ import annotations

import re
from typing import TypedDict

from sec_alphaops_common.config.filing_registry import FilingTypeProfile
from sec_alphaops_common.config.prompt_store import PromptTemplateStore

from sec_alphaops_langgraph.llm import invoke_json


class GraphState(TypedDict, total=False):
    ticker: str
    filing_type: str
    chunks: list[dict]
    sections: list[dict]
    risk_factors: list[dict]
    kpi_data: list[dict]
    confidence: float
    rationale: str
    citations: list[dict]
    provenance_ids: list[str]
    policy_flags: list[str]
    prompt_version: str | None


SECTION_PATTERNS = {
    "Item 1A": re.compile(r"item\s*1a[\.\s\-]*risk\s*factors", re.I),
    "Item 7": re.compile(r"item\s*7[\.\s\-]*", re.I),
    "Item 8": re.compile(r"item\s*8[\.\s\-]*", re.I),
}


def _heuristic_sections(text: str) -> list[dict]:
    sections = []
    for label, pattern in SECTION_PATTERNS.items():
        m = pattern.search(text)
        if m:
            start = m.start()
            sections.append({"label": label, "start_offset": start, "text": text[start : start + 4000]})
    if not sections and text:
        sections.append({"label": "full", "start_offset": 0, "text": text[:8000]})
    return sections


async def section_classifier(state: GraphState, profile: FilingTypeProfile, prompts: PromptTemplateStore) -> dict:
    combined = "\n".join(c["text"] for c in state.get("chunks", []) if c.get("text"))
    sections = _heuristic_sections(combined)
    prompt = prompts.load(profile.filing_type, "sectionClassifier", state.get("prompt_version"))
    prompt = prompt.replace("{{ ticker }}", state.get("ticker", "")).replace("{{ text }}", combined[:6000])
    llm_sections = await invoke_json(prompt, profile.model_tiers.get("sectionClassifier", "gpt-4.1-nano"))
    if llm_sections.get("sections"):
        sections = llm_sections["sections"]
    return {"sections": sections, "provenance_ids": [f"chunk:{i}" for i in range(len(state.get("chunks", [])))]}


async def risk_extractor(state: GraphState, profile: FilingTypeProfile, prompts: PromptTemplateStore) -> dict:
    risks = []
    citations = []
    for sec in state.get("sections", []):
        if "1A" not in sec.get("label", "") and sec.get("label") != "full":
            continue
        text = sec.get("text", "")
        prompt = prompts.load(profile.filing_type, "riskExtractor", state.get("prompt_version"))
        prompt = prompt.replace("{{ ticker }}", state.get("ticker", "")).replace("{{ text }}", text[:6000])
        data = await invoke_json(prompt, profile.model_tiers.get("riskExtractor", "gpt-4.1-mini"))
        for rf in data.get("risk_factors", []):
            risks.append(rf)
            citations.extend(rf.get("citations", []))
        if not data.get("risk_factors") and text:
            risks.append(
                {
                    "title": "Identified risk (heuristic)",
                    "summary": text[:500],
                    "severity": "medium",
                    "citations": [{"section": sec.get("label", ""), "excerpt": text[:200]}],
                }
            )
    return {"risk_factors": risks, "citations": citations}


async def kpi_extractor(state: GraphState, profile: FilingTypeProfile, prompts: PromptTemplateStore) -> dict:
    kpis = []
    for sec in state.get("sections", []):
        if "8" not in sec.get("label", "") and "7" not in sec.get("label", "") and sec.get("label") != "full":
            continue
        text = sec.get("text", "")
        for line in text.splitlines():
            if re.search(r"\$[\d,]+|\d+\.\d+%|revenue|net income", line, re.I):
                kpis.append(
                    {
                        "metric": line.strip()[:80],
                        "value": line.strip()[:120],
                        "period": None,
                        "citations": [{"section": sec.get("label", ""), "excerpt": line[:200]}],
                    }
                )
                if len(kpis) >= 10:
                    break
    return {"kpi_data": kpis[:10]}


async def cross_check_node(state: GraphState, profile: FilingTypeProfile, _prompts: PromptTemplateStore) -> dict:
    flags = []
    if state.get("risk_factors") and not state.get("citations"):
        flags.append("missing_citations")
    if len(state.get("kpi_data", [])) == 0:
        flags.append("no_kpis_extracted")
    return {"policy_flags": flags, "rationale": "Cross-section consistency checks applied."}


async def confidence_scorer(state: GraphState, profile: FilingTypeProfile, _prompts: PromptTemplateStore) -> dict:
    base = 0.9
    if not state.get("risk_factors"):
        base -= 0.25
    if state.get("policy_flags"):
        base -= 0.15 * len(state["policy_flags"])
    if not state.get("kpi_data"):
        base -= 0.1
    confidence = max(0.0, min(1.0, base))
    return {"confidence": confidence}


async def policy_guard(state: GraphState, profile: FilingTypeProfile, _prompts: PromptTemplateStore) -> dict:
    flags = list(state.get("policy_flags", []))
    if state.get("confidence", 0) < profile.confidence_threshold:
        flags.append("low_confidence")
    for rf in state.get("risk_factors", []):
        if not rf.get("citations"):
            flags.append("risk_without_citation")
            break
    return {"policy_flags": list(dict.fromkeys(flags))}


NODE_FUNCS = {
    "sectionClassifier": section_classifier,
    "riskExtractor": risk_extractor,
    "kpiExtractor": kpi_extractor,
    "crossCheckNode": cross_check_node,
    "confidenceScorer": confidence_scorer,
    "policyGuard": policy_guard,
}
