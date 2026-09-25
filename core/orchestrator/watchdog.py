"""Task Watchdog & Stuck Task Detection for Phase 20 (Shivani 1.0).

Monitors execution progress, detects runaway loops, repeated failures,
endless retries, and transitions stalled tasks to safe terminal or paused states.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional

from core.orchestrator.state_machine import Task, TaskState
try:
    from core.tasks.task import TaskStatus
except ImportError:
    TaskStatus = None

logger = logging.getLogger("shivani.watchdog")


class TaskWatchdog:
    """Proactively inspects task progress to prevent infinite loops, deadlocks, and hung operations."""

    def __init__(
        self,
        task: Optional[Any] = None,
        max_no_progress_sec: float = 90.0,
        max_repeated_actions: int = 3,
        max_repeated_errors: int = 3,
        max_step_retries: int = 5,
        max_steps: int = 25,
    ):
        self._task = task
        self.max_no_progress_sec = max_no_progress_sec
        self.max_repeated_actions = max_repeated_actions
        self.max_repeated_errors = max_repeated_errors
        self.max_step_retries = max_step_retries
        self.max_steps = max_steps

        self._last_progress_timestamp: Dict[str, float] = {}
        self._action_history: Dict[str, List[str]] = {}
        self._error_history: Dict[str, List[str]] = {}

    def record_activity(self, task_id: str, action_name: Optional[str] = None, error: Optional[str] = None) -> None:
        """Update last recorded activity for a task."""
        now = time.time()
        self._last_progress_timestamp[task_id] = now

        if action_name:
            history = self._action_history.setdefault(task_id, [])
            history.append(action_name)
            if len(history) > 50:
                history.pop(0)

        if error:
            err_list = self._error_history.setdefault(task_id, [])
            err_list.append(error.strip()[:100])
            if len(err_list) > 20:
                err_list.pop(0)

    def record_action(self, action_name: str, arguments: Optional[Dict[str, Any]] = None, task_id: Optional[str] = None) -> bool:
        """Records an action for the bound task, returning False if watchdog halted the task."""
        tid = task_id or (self._task.id if self._task else "default")
        self.record_activity(tid, action_name=action_name)
        if self._task:
            if hasattr(self._task, "current_step_index"):
                self._task.current_step_index += 1
            is_stuck, _ = self.check_task(self._task)
            return not is_stuck
        return True

    def record_error(self, error: str, task_id: Optional[str] = None) -> None:
        """Records an error for the bound task and checks threshold."""
        tid = task_id or (self._task.id if self._task else "default")
        self.record_activity(tid, error=error)
        if self._task:
            self.check_task(self._task)

    def check_health(self) -> Tuple[bool, Optional[str]]:
        """Checks health of the bound task."""
        if self._task:
            return self.check_task(self._task)
        return False, None

    def check_task(self, task: Task) -> Tuple[bool, Optional[str]]:
        """Inspect a task for stalled or pathological execution patterns.

        Returns:
            Tuple of (is_stuck, reason)
        """
        current_state = getattr(task, "state", None) or getattr(task, "status", None)
        if current_state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELLED):
            return False, None
        if str(current_state).upper().endswith("BLOCKED") or str(current_state).upper().endswith("PAUSED"):
            return True, getattr(task, "error", f"Task is halted in {current_state} state.")

        now = time.time()
        last_activity = self._last_progress_timestamp.get(task.id, now)

        # 1. No Progress Timeout
        if (now - last_activity) > self.max_no_progress_sec:
            reason = f"No activity observed for {int(now - last_activity)}s (exceeds {self.max_no_progress_sec}s threshold)."
            self._transition_to_safe_state(task, reason)
            return True, reason

        # 2. Repeated Consecutive Actions (Loop Detection)
        actions = self._action_history.get(task.id, [])
        if len(actions) >= self.max_repeated_actions:
            last_n = actions[-self.max_repeated_actions:]
            if len(set(last_n)) == 1:
                reason = f"Repeated action loop detected: repeated '{last_n[0]}' {self.max_repeated_actions} consecutive times."
                self._transition_to_safe_state(task, reason)
                return True, reason

        # 3. Repeated Consecutive Errors
        errors = self._error_history.get(task.id, [])
        if len(errors) >= self.max_repeated_errors:
            last_errs = errors[-self.max_repeated_errors:]
            if len(set(last_errs)) == 1:
                reason = f"Repeated error threshold exceeded: '{last_errs[0]}' failed {self.max_repeated_errors} consecutive times."
                self._transition_to_safe_state(task, reason)
                return True, reason

        # 4. Step Count Limit
        if getattr(task, "current_step_index", 0) >= self.max_steps:
            reason = f"Step limit exceeded ({self.max_steps} steps)."
            self._transition_to_safe_state(task, reason)
            return True, reason

        return False, None

    def _transition_to_safe_state(self, task: Any, reason: str) -> None:
        """Safely halt runaway task."""
        task_id = getattr(task, "id", "unknown")
        logger.warning(f"TaskWatchdog triggering safe state for task {task_id}: {reason}")
        if hasattr(task, "transition_to"):
            try:
                task.transition_to(
                    TaskState.BLOCKED,
                    message=f"[TaskWatchdog Safeguard]: {reason}",
                    details={"watchdog_reason": reason, "timestamp": time.time()},
                )
            except Exception:
                pass
        if hasattr(task, "state"):
            task.state = TaskState.BLOCKED
        if hasattr(task, "status"):
            task.status = TaskStatus.BLOCKED if TaskStatus else "BLOCKED"
        task.error = reason

    def cleanup(self, task_id: str) -> None:
        """Purge tracking data for completed task."""
        self._last_progress_timestamp.pop(task_id, None)
        self._action_history.pop(task_id, None)
        self._error_history.pop(task_id, None)
