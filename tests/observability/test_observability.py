"""
Phase 9 Observability Test Suite
Verifies metrics collection, distributed tracing, health evaluation,
and doctor diagnostics.
"""

import time
import pytest

from observability.metrics import MetricsCollector
from observability.tracing import Tracer
from observability.health import HealthChecker, HealthStatus
from observability.diagnostics import DiagnosticsRunner
from observability.performance import PerformanceProfiler


def test_metrics_collection_and_percentiles():
    mc = MetricsCollector()

    # Counters
    mc.increment("task.count", 1.0)
    mc.increment("task.count", 2.0)
    assert mc.get_counter("task.count") == 3.0

    # Latencies
    latencies = [0.05, 0.10, 0.15, 0.20, 0.50]
    for lat in latencies:
        mc.record_latency("llm.generate", lat)

    stats = mc.get_latency_stats("llm.generate")
    assert stats["count"] == 5
    assert stats["min"] == 0.05
    assert stats["max"] == 0.50
    assert 0.15 <= stats["avg"] <= 0.25


def test_tracer_nested_spans():
    tracer = Tracer()

    with tracer.start_span("parent_span", tags={"phase": "9"}) as p_span:
        time.sleep(0.01)
        with tracer.start_span("child_span", tags={"step": "1"}) as c_span:
            time.sleep(0.01)
            assert c_span.parent_id == p_span.span_id
            assert c_span.trace_id == p_span.trace_id

    spans = tracer.get_recent_spans(limit=10)
    names = [s["name"] for s in spans]
    assert "child_span" in names
    assert "parent_span" in names


def test_health_checker_operational_status():
    hc = HealthChecker()
    report = hc.check_overall_health()

    assert "overall_status" in report
    assert report["overall_status"] in [HealthStatus.ONLINE.value, HealthStatus.DEGRADED.value]
    assert "storage" in report["components"]
    assert "security" in report["components"]
    assert "tools" in report["components"]


def test_diagnostics_quick_and_full():
    diag = DiagnosticsRunner()

    quick_items = diag.run_quick_doctor()
    assert len(quick_items) >= 4
    names = [item.name for item in quick_items]
    assert "Operating System" in names
    assert "Python Version" in names

    full_items = diag.run_full_doctor()
    assert len(full_items) >= len(quick_items)
    full_names = [item.name for item in full_items]
    assert "Tool Registry" in full_names


def test_performance_profiler_snapshot():
    prof = PerformanceProfiler()
    summary = prof.get_summary()

    assert "pid" in summary
    assert "memory_mb" in summary
    assert summary["memory_mb"] > 0
