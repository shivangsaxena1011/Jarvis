"""
SHIVANI Observability — Performance & Resource Profiler
Monitors memory usage, CPU load, and active background threads/tasks.
"""

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class ResourceSnapshot:
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    timestamp: float


class PerformanceProfiler:
    """Profiles memory and CPU consumption for the current process."""

    def __init__(self):
        self._process = None
        try:
            import psutil
            self._process = psutil.Process(os.getpid())
        except Exception:
            pass

    def get_snapshot(self) -> ResourceSnapshot:
        if self._process is not None:
            try:
                mem_info = self._process.memory_info()
                cpu = self._process.cpu_percent(interval=None)
                mem_mb = mem_info.rss / (1024 * 1024)
                mem_pct = self._process.memory_percent()
                return ResourceSnapshot(cpu_percent=cpu, memory_mb=mem_mb, memory_percent=mem_pct, timestamp=time.time())
            except Exception:
                pass
        return ResourceSnapshot(cpu_percent=0.0, memory_mb=0.0, memory_percent=0.0, timestamp=time.time())

    def get_summary(self) -> Dict[str, Any]:
        snap = self.get_snapshot()
        return {
            "pid": os.getpid(),
            "cpu_percent": snap.cpu_percent,
            "memory_mb": round(snap.memory_mb, 2),
            "memory_percent": round(snap.memory_percent, 2),
            "timestamp": snap.timestamp,
        }


PROFILER = PerformanceProfiler()
