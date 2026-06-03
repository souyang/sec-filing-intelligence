from __future__ import annotations

import asyncio

from sec_alphaops_workflows import (
    BatchOrchestratorWorkflow,
    CacheHydrateWorkflow,
    FilingProcessingWorkflow,
    HumanReviewWorkflow,
    ReprocessingWorkflow,
)
from temporalio.client import Client
from temporalio.worker import Worker

from sec_alphaops_worker.activities import (
    bulk_download,
    create_review_task,
    emit_filing_stage,
    ensure_filing_record,
    fetch_filing,
    langgraph_analysis,
    parse_chunk,
    persist_insights,
    publish_run_event,
    set_run_status,
    sync_cache_to_r2,
    update_run_counters,
)
from sec_alphaops_worker.settings import settings


async def main() -> None:
    client = await Client.connect(
        settings.temporal_address,
        namespace=settings.temporal_namespace,
    )
    worker = Worker(
        client,
        task_queue=settings.temporal_task_queue,
        workflows=[
            BatchOrchestratorWorkflow,
            CacheHydrateWorkflow,
            FilingProcessingWorkflow,
            HumanReviewWorkflow,
            ReprocessingWorkflow,
        ],
        activities=[
            bulk_download,
            sync_cache_to_r2,
            ensure_filing_record,
            fetch_filing,
            parse_chunk,
            langgraph_analysis,
            create_review_task,
            persist_insights,
            publish_run_event,
            update_run_counters,
            emit_filing_stage,
            set_run_status,
        ],
    )
    print(f"Worker polling task queue: {settings.temporal_task_queue}")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
