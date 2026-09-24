"""
SHIVANI Observability — Metrics Subsystem
Collects latencies, counters, error rates, and resource utilization metrics.
"""

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import threading


@dataclass
class MetricRecord:
    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: Dict[str, str] = field(default_factory=dict)


class MetricsCollector:
    """Thread-safe collector for runtime performance and execution metrics."""

    def __init__(self):
        self._lock = threading.Lock()
        self._counters: Dict[str, float] = defaultdict(float)
        self._latencies: Dict[str, List[float]] = defaultdict(list)
        self._records: List[MetricRecord] = []
        self._max_history = 1000

    def increment(self, metric: str, amount: float = 1.0, tags: Optional[Dict[str, str]] = None) -> None:
        """Increments a counter metric."""
        with self._lock:
            self._counters[metric] += amount
            self._records.append(MetricRecord(name=metric, value=amount, tags=tags or {}))
            if len(self._records) > self._max_history:
                self._records = self._records[-self._max_history:]

    def record_latency(self, metric: str, latency_seconds: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Records an execution latency value in seconds."""
        with self._lock:
            self._latencies[metric].append(latency_seconds)
            # Keep last 500 samples per metric
            if len(self._latencies[metric]) > 500:
                self._latencies[metric] = self._latencies[metric][-500:]
            self._records.append(MetricRecord(name=f"{metric}.latency", value=latency_seconds, tags=tags or {}))

    def get_counter(self, metric: str) -> float:
        with self._lock:
            return self._counters.get(metric, 0.0)

    def get_latency_stats(self, metric: str) -> Dict[str, float]:
        with self._lock:
            samples = self._latencies.get(metric, [])
            if not samples:
                return {"count": 0, "avg": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
            sorted_samples = sorted(samples)
            count = len(sorted_samples)
            p95_idx = min(count - 1, int(count * 0.95))
            return {
                "count": count,
                "avg": sum(sorted_samples) / count,
                "min": sorted_samples[0],
                "max": sorted_samples[-1],
                "p95": sorted_samples[p95_idx],
            }

    def get_summary(self) -> Dict[str, Any]:
        """Returns snapshot of current metrics summary."""
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "latencies": {
                    name: self.get_latency_stats(name)
                    for name in self._latencies.keys()
                },
                "total_records": len(self._records),
            }
            return summary

    def reset(self) -> None:
        with self._lock:
            self._counters.clear()
            self._latencies.clear()
            self._records.clear()


# Global metrics instance
METRICS = MetricsCollector()
