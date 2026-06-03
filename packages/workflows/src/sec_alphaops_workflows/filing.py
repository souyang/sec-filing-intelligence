from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from sec_alphaops_common.config.run_profile import RunProfile

    from sec_alphaops_workflows.activities.filing import (
        CreateReviewTaskActivity,
        EnsureFilingRecordActivity,
        FetchFilingActivity,
        LangGraphAnalysisActivity,
        ParseChunkActivity,
        PersistInsightsActivity,
    )
    from sec_alphaops_workflows.activities.run_events import (
        EmitFilingStageActivity,
        UpdateRunCountersActivity,
    )
    from sec_alphaops_workflows.human_review import HumanReviewInput, HumanReviewWorkflow


@dataclass
class FilingProcessingInput:
    run_id: str
    ticker: str
    year: int
    filing_type: str
    profile: dict[str, Any]


@workflow.defn(name="FilingProcessingWorkflow")
class FilingProcessingWorkflow:
    @workflow.run
    async def run(self, input: FilingProcessingInput) -> dict[str, Any]:
        retry = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_attempts=5,
        )
        profile = RunProfile.model_validate(input.profile)
        threshold = profile.confidence_thresholds.get("default", 0.75)

        record = await workflow.execute_activity(
            EnsureFilingRecordActivity,
            {
                "run_id": input.run_id,
                "ticker": input.ticker,
                "year": input.year,
                "filing_type": input.filing_type,
                "profile": input.profile,
            },
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry,
        )
        filing_id = record["filing_id"]
        activity_input = {
            "run_id": input.run_id,
            "ticker": input.ticker,
            "year": input.year,
            "filing_type": input.filing_type,
            "profile": input.profile,
            "filing_id": filing_id,
        }

        await workflow.execute_activity(
            EmitFilingStageActivity,
            {
                "run_id": input.run_id,
                "filing_id": filing_id,
                "ticker": input.ticker,
                "stage": "fetch",
                "status": "running",
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        raw = await workflow.execute_activity(
            FetchFilingActivity,
            activity_input,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry,
        )

        await workflow.execute_activity(
            EmitFilingStageActivity,
            {
                "run_id": input.run_id,
                "filing_id": filing_id,
                "ticker": input.ticker,
                "stage": "parse",
                "status": "running",
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        chunks = await workflow.execute_activity(
            ParseChunkActivity,
            {"raw": raw, "input": activity_input},
            start_to_close_timeout=timedelta(minutes=15),
            retry_policy=retry,
        )

        await workflow.execute_activity(
            EmitFilingStageActivity,
            {
                "run_id": input.run_id,
                "filing_id": filing_id,
                "ticker": input.ticker,
                "stage": "analyze",
                "status": "running",
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        analysis = await workflow.execute_activity(
            LangGraphAnalysisActivity,
            {"chunks": chunks, "input": activity_input},
            start_to_close_timeout=timedelta(minutes=30),
            heartbeat_timeout=timedelta(minutes=2),
            retry_policy=retry,
        )

        confidence = float(analysis.get("confidence", 0.0))
        policy_flags = analysis.get("policy_flags", [])
        needs_review = (
            profile.hitl_mode == "review_all"
            or (
                profile.hitl_mode == "threshold_based"
                and (confidence < threshold or bool(policy_flags))
            )
        )

        if needs_review and profile.hitl_mode != "auto_approve_all":
            review_wf_id = f"review-{input.run_id}-{input.ticker}-{input.year}"
            await workflow.execute_activity(
                CreateReviewTaskActivity,
                {
                    "input": activity_input,
                    "analysis": analysis,
                    "temporal_workflow_id": review_wf_id,
                },
                start_to_close_timeout=timedelta(minutes=2),
                retry_policy=retry,
            )
            review_result = await workflow.execute_child_workflow(
                HumanReviewWorkflow.run,
                HumanReviewInput(
                    run_id=input.run_id,
                    ticker=input.ticker,
                    filing_id=filing_id,
                    analysis=analysis,
                ),
                id=review_wf_id,
            )
            analysis = review_result.get("analysis", analysis)

        await workflow.execute_activity(
            PersistInsightsActivity,
            {"analysis": analysis, "input": activity_input},
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry,
        )

        await workflow.execute_activity(
            EmitFilingStageActivity,
            {
                "run_id": input.run_id,
                "filing_id": filing_id,
                "ticker": input.ticker,
                "stage": "persist",
                "status": "completed",
            },
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=retry,
        )

        await workflow.execute_activity(
            UpdateRunCountersActivity,
            {"run_id": input.run_id, "increment": True, "failed": False},
            start_to_close_timeout=timedelta(minutes=2),
            retry_policy=retry,
        )
        return analysis
