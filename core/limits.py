"""
SHIVANI Resource & Execution Limits
Defines runtime constraints to prevent runaway loops, resource exhaustion,
and excessive tool or token usage.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExecutionLimits:
    max_task_duration_seconds: float = 600.0  # 10 minutes default
    max_tool_calls_per_task: int = 50
    max_retries_per_step: int = 3
    max_browser_tabs: int = 5
    max_file_size_bytes: int = 50 * 1024 * 1024  # 50 MB
    max_memory_mb: int = 2048  # 2 GB
    max_concurrent_tasks: int = 5
    step_timeout_seconds: float = 60.0
    command_timeout_seconds: float = 30.0

    def check_duration(self, elapsed_seconds: float) -> bool:
        """Returns True if within execution time limit."""
        return elapsed_seconds <= self.max_task_duration_seconds

    def check_tool_calls(self, current_calls: int) -> bool:
        """Returns True if within tool call budget."""
        return current_calls < self.max_tool_calls_per_task

    def check_browser_tabs(self, active_tabs: int) -> bool:
        """Returns True if within browser tab limit."""
        return active_tabs < self.max_browser_tabs

    def check_file_size(self, size_bytes: int) -> bool:
        """Returns True if file is within permissible size limit."""
        return size_bytes <= self.max_file_size_bytes


# Global default limits
DEFAULT_LIMITS = ExecutionLimits()
