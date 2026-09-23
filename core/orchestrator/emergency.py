"""
SHIVANI Emergency Stop System
Provides immediate abort mechanism across all active tasks and sub-processes.
Responds to "Shivani stop" voice command and Desktop UI Emergency STOP button.
"""

import asyncio
from typing import Set


class EmergencyStop:
    def __init__(self):
        self._is_stopped = False
        self._stopped_tasks: Set[str] = set()
        self._active_async_tasks: dict[str, asyncio.Task] = {}

    @property
    def is_stopped(self) -> bool:
        return self._is_stopped

    def register_task(self, task_id: str, async_task: asyncio.Task) -> None:
        self._active_async_tasks[task_id] = async_task

    def unregister_task(self, task_id: str) -> None:
        self._active_async_tasks.pop(task_id, None)

    def trigger_stop_all(self) -> int:
        """Immediately aborts all running tasks and sets emergency stop state."""
        self._is_stopped = True
        cancelled_count = 0

        for task_id, async_task in list(self._active_async_tasks.items()):
            if not async_task.done():
                async_task.cancel()
                self._stopped_tasks.add(task_id)
                cancelled_count += 1

        self._active_async_tasks.clear()
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
