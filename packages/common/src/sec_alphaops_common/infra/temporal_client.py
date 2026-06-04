from __future__ import annotations

from typing import Any

from temporalio.client import Client

from sec_alphaops_common.settings import BaseServiceSettings

_clients: dict[tuple[str, str, bool], Client] = {}


async def get_temporal_client(
    address: str,
    namespace: str,
    api_key: str | None = None,
) -> Client:
    """Connect to Temporal Server or Temporal Cloud (API key enables TLS automatically)."""
    cache_key = (address, namespace, bool(api_key))
    if cache_key not in _clients:
        if api_key:
            _clients[cache_key] = await Client.connect(
                address,
                namespace=namespace,
                api_key=api_key,
            )
        else:
            _clients[cache_key] = await Client.connect(address, namespace=namespace)
    return _clients[cache_key]


async def get_temporal_client_from_settings(settings: BaseServiceSettings) -> Client:
    return await get_temporal_client(
        settings.temporal_address,
        settings.temporal_namespace,
        settings.temporal_api_key,
    )


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
