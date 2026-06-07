from __future__ import annotations

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class TraceEvent:
    name: str
    status: str
    elapsed_ms: float | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class TraceLog:
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    events: list[TraceEvent] = field(default_factory=list)

    @contextmanager
    def step(self, name: str, **inputs: Any) -> Iterator[TraceEvent]:
        event = TraceEvent(name=name, status="running", inputs=_compact(inputs))
        started = time.perf_counter()
        self.events.append(event)
        try:
            yield event
            event.status = "ok"
        except Exception as exc:
            event.status = "error"
            event.error = str(exc)
            raise
        finally:
            event.elapsed_ms = round((time.perf_counter() - started) * 1000, 2)

    def add_event(
        self,
        name: str,
        status: str = "ok",
        inputs: dict[str, Any] | None = None,
        outputs: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        self.events.append(
            TraceEvent(
                name=name,
                status=status,
                inputs=_compact(inputs or {}),
                outputs=_compact(outputs or {}),
                error=error,
            )
        )

    def as_records(self) -> list[dict[str, Any]]:
        return [
            {
                "step": event.name,
                "status": event.status,
                "elapsed_ms": event.elapsed_ms,
                "inputs": event.inputs,
                "outputs": event.outputs,
                "error": event.error,
            }
            for event in self.events
        ]


def _compact(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _compact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_compact(item) for item in value[:20]]
    if hasattr(value, "shape") and hasattr(value, "columns"):
        return {
            "rows": int(value.shape[0]),
            "columns": [str(column) for column in value.columns],
        }
    text = str(value)
    if len(text) > 1200:
        return text[:1200] + "...[truncated]"
    return value

