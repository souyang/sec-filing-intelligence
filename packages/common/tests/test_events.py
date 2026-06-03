from sec_alphaops_common.events.sse import RunCounterEvent, export_sse_json_schema


def test_sse_schema_export() -> None:
    schema = export_sse_json_schema()
    assert "$defs" in schema or "oneOf" in schema or "anyOf" in schema


def test_run_counter_event() -> None:
    from uuid import uuid4

    ev = RunCounterEvent(run_id=uuid4(), completed=1, failed=0)
    dumped = ev.model_dump(mode="json")
    assert dumped["type"] == "run.counters"
    assert dumped["completed"] == 1
