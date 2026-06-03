from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow


@dataclass
class HumanReviewInput:
    run_id: str
    ticker: str
    filing_id: str
    analysis: dict[str, Any]


@dataclass
class ReviewDecision:
    action: str  # approve | edit_approve | reject
    edited_analysis: dict[str, Any] | None = None
    note: str | None = None


@workflow.defn(name="HumanReviewWorkflow")
class HumanReviewWorkflow:
    def __init__(self) -> None:
        self._decision: ReviewDecision | None = None

    @workflow.run
    async def run(self, input: HumanReviewInput) -> dict[str, Any]:
        await workflow.wait_condition(lambda: self._decision is not None, timeout=timedelta(days=7))
        decision = self._decision
        assert decision is not None

        analysis = dict(input.analysis)
        if decision.action == "reject":
            analysis["status"] = "rejected"
            analysis["review_note"] = decision.note
            return {"analysis": analysis, "decision": decision.action}

        if decision.action == "edit_approve" and decision.edited_analysis:
            analysis.update(decision.edited_analysis)

        analysis["status"] = "approved"
        analysis["review_note"] = decision.note
        return {"analysis": analysis, "decision": decision.action}

    @workflow.update
    async def submit_review(self, decision: ReviewDecision) -> str:
        self._decision = decision
        return f"accepted:{decision.action}"
