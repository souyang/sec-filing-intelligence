from __future__ import annotations

from functools import lru_cache
from typing import Any

from temporalio.client import Client


@lru_cache(maxsize=1)
def _client_cache_key(address: str, namespace: str) -> tuple[str, str]:
    return address, namespace


_clients: dict[tuple[str, str], Client] = {}


async def get_temporal_client(address: str, namespace: str) -> Client:
    key = (address, namespace)
    if key not in _clients:
        _clients[key] = await Client.connect(address, namespace=namespace)
    return _clients[key]


async def start_workflow(
    client: Client,
    workflow_run: Any,
    arg: Any,
    *,
    workflow_id: str,
    task_queue: str,
) -> str:
    handle = await client.start_workflow(
        workflow_run,
        arg,
        id=workflow_id,
        task_queue=task_queue,
    )
    return handle.id


async def execute_update(
    client: Client,
    workflow_id: str,
    update_name: str,
    arg: Any,
) -> Any:
    handle = client.get_workflow_handle(workflow_id)
    return await handle.execute_update(update_name, arg)
