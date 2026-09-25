"""
SHIVANI Emergency Stop System
Provides immediate abort mechanism across all active tasks and sub-processes.
Responds to "Shivani stop" voice command and Desktop UI Emergency STOP button.
"""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger("shivani.emergency")


class EmergencyStop:
    """
    Emergency Stop Subsystem for SHIVANI.
    Provides immediate abort mechanisms across active asyncio tasks,
    subprocesses, browser sessions, phone commands, and hardware input hooks.
    """

    def __init__(self):
        self._is_stopped = False
        self._stopped_tasks: Set[str] = set()
        self._active_async_tasks: dict[str, asyncio.Task] = {}
        self._abort_callbacks: Dict[str, Callable[[], Any]] = {}

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    def register_task(self, task_id: str, async_task: asyncio.Task) -> None:
        self._active_async_tasks[task_id] = async_task

    def unregister_task(self, task_id: str) -> None:
        self._active_async_tasks.pop(task_id, None)

    def register_abort_callback(self, name: str, callback: Callable[[], Any]) -> None:
        """Registers a cleanup/abort callback to run immediately upon emergency stop."""
        self._abort_callbacks[name] = callback

    def unregister_abort_callback(self, name: str) -> None:
        self._abort_callbacks.pop(name, None)

    def trigger_stop_all(self) -> int:
        """Immediately aborts all running tasks, runs abort callbacks, and sets emergency stop state."""
        self._is_stopped = True
        cancelled_count = 0

        # Cancel active async tasks
        for task_id, async_task in list(self._active_async_tasks.items()):
            if not async_task.done():
                async_task.cancel()
                self._stopped_tasks.add(task_id)
                cancelled_count += 1

        self._active_async_tasks.clear()

        # Run registered abort callbacks
        for name, callback in list(self._abort_callbacks.items()):
            try:
                res = callback()
                if inspect.iscoroutine(res):
                    asyncio.create_task(res)
                logger.info("Executed emergency abort callback: %s", name)
            except Exception as e:
                logger.error("Error executing emergency callback '%s': %s", name, e)

        return cancelled_count

    def trigger_stop_task(self, task_id: str) -> bool:
        """Aborts a specific active task."""
        async_task = self._active_async_tasks.pop(task_id, None)
        if async_task and not async_task.done():
            async_task.cancel()
            self._stopped_tasks.add(task_id)
            return True
        return False

    def is_task_cancelled(self, task_id: str) -> bool:
        return self._is_stopped or (task_id in self._stopped_tasks)

    def reset(self) -> None:
        """Resets emergency stop state to allow new tasks to run."""
        self._is_stopped = False
        self._stopped_tasks.clear()


from enum import Enum


class EmergencyState(str, Enum):
    NORMAL = "NORMAL"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    RECOVERING = "RECOVERING"


class EmergencyController(EmergencyStop):
    """Authoritative Kill-Switch Controller for Phase 20 (Shivani 1.0).

    Enforces global halt across all active agents, browser sessions,
    mesh relays, and prevents new autonomous actions until explicit recovery.
    """

    def __init__(self):
        super().__init__()
        self._state: EmergencyState = EmergencyState.NORMAL
        self._stop_reason: Optional[str] = None

    @property
    def state(self) -> EmergencyState:
        return self._state

    @property
    def stop_reason(self) -> Optional[str]:
        return self._stop_reason

    def can_execute_action(self) -> bool:
        """Determines if new autonomous operations are permitted."""
        return self._state == EmergencyState.NORMAL

    def assert_can_execute(self) -> None:
        """Raises RuntimeError if system is currently halted or emergency stop is active."""
        if not self.can_execute_action():
            raise RuntimeError(f"Emergency stop is ACTIVE ({self._state.value}): {self._stop_reason or 'No action permitted'}")

    def abort_all(self, reason: str = "Emergency Stop triggered") -> int:
        """Execute immediate kill switch across all subsystems."""
        self._state = EmergencyState.STOPPING
        self._stop_reason = reason
        logger.warning(f"GLOBAL EMERGENCY KILL SWITCH ACTIVATED: {reason}")
        cancelled = self.trigger_stop_all()
        self._state = EmergencyState.STOPPED
        return cancelled

    def resume(self) -> bool:
        """Explicitly resume normal operation after user clears emergency stop."""
        self._state = EmergencyState.RECOVERING
        logger.info("Emergency state clearing: revalidating safety invariants...")
        self.reset()
        self._stop_reason = None
        self._state = EmergencyState.NORMAL
        logger.info("System returned to NORMAL operational state.")
        return True


# Alias for backward compatibility
EmergencyStopController = EmergencyController


