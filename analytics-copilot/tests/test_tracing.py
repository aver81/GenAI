import pytest

from analytics_copilot.tracing import TraceLog


def test_trace_log_records_successful_step():
    trace = TraceLog()

    with trace.step("example", question="hello") as event:
        event.outputs = {"answer": "world"}

    records = trace.as_records()
    assert records[0]["step"] == "example"
    assert records[0]["status"] == "ok"
    assert records[0]["elapsed_ms"] >= 0
    assert records[0]["inputs"] == {"question": "hello"}
    assert records[0]["outputs"] == {"answer": "world"}


def test_trace_log_records_error_step():
    trace = TraceLog()

    with pytest.raises(ValueError):
        with trace.step("boom"):
            raise ValueError("bad thing")

    records = trace.as_records()
    assert records[0]["status"] == "error"
    assert records[0]["error"] == "bad thing"

