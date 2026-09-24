"""
SHIVANI Observability — Distributed / Local Tracing
Provides lightweight span tracking and context propagation across orchestrator,
agents, tools, and background tasks.
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional
import threading


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    parent_id: Optional[str] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    duration: float = 0.0
    tags: Dict[str, Any] = field(default_factory=dict)
    status: str = "RUNNING"  # "SUCCESS", "ERROR", "CANCELLED"
    error: Optional[str] = None

    def finish(self, status: str = "SUCCESS", error: Optional[str] = None) -> None:
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.status = status
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "tags": self.tags,
            "status": self.status,
            "error": self.error,
        }


class Tracer:
    """Manages active trace spans and history."""

    def __init__(self):
        self._local = threading.local()
        self._completed_spans: List[Span] = []
        self._lock = threading.Lock()
        self._max_history = 1000

    def _get_active_stack(self) -> List[Span]:
        if not hasattr(self._local, "stack"):
            self._local.stack = []
        return self._local.stack

    @contextmanager
    def start_span(self, name: str, tags: Optional[Dict[str, Any]] = None) -> Iterator[Span]:
        stack = self._get_active_stack()
        parent = stack[-1] if stack else None

        trace_id = parent.trace_id if parent else uuid.uuid4().hex[:16]
        parent_id = parent.span_id if parent else None

        span = Span(name=name, trace_id=trace_id, parent_id=parent_id, tags=tags or {})
        stack.append(span)

        try:
            yield span
            if span.status == "RUNNING":
                span.finish(status="SUCCESS")
        except Exception as e:
            span.finish(status="ERROR", error=str(e))
            raise
        finally:
            if stack and stack[-1] is span:
                stack.pop()
            with self._lock:
                self._completed_spans.append(span)
                if len(self._completed_spans) > self._max_history:
                    self._completed_spans = self._completed_spans[-self._max_history:]

    def get_spans_for_trace(self, trace_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.to_dict() for s in self._completed_spans if s.trace_id == trace_id]

    def get_recent_spans(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._lock:
            return [s.to_dict() for s in self._completed_spans[-limit:]]

    def clear(self) -> None:
        with self._lock:
            self._completed_spans.clear()


# Global tracer instance
TRACER = Tracer()
