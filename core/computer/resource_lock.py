"""
SHIVANI Resource Lock & Computer Action Priority Manager (Phase 17).
Provides cooperative and preemptive resource locking across Desktop, Browser,
Terminal, VS Code, and Clipboard with a strict priority hierarchy.
"""

from __future__ import annotations
import asyncio
from enum import IntEnum
import time
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class ActionPriority(IntEnum):
    EMERGENCY_STOP = 100
    DIRECT_USER_COMMAND = 80
    USER_APPROVED_TASK = 60
    INTERACTIVE_AUTOMATION = 40
    SCHEDULED_AUTOMATION = 20
    BACKGROUND_AUTOMATION = 10


class LockHolder(BaseModel):
    holder_id: str
    priority: ActionPriority
    acquired_at: float = Field(default_factory=time.time)
    reason: str = ""


class ResourceLockManager:
    """Manages exclusive access to physical desktop input and resources."""

    VALID_RESOURCES = {"Desktop", "Browser", "Terminal", "VSCode", "FileSystem", "Clipboard"}

    def __init__(self):
        self._locks: Dict[str, Optional[LockHolder]] = {r: None for r in self.VALID_RESOURCES}
        self._emergency_stopped: bool = False
        self._manual_takeover: bool = False

    @property
    def is_emergency_stopped(self) -> bool:
        return self._emergency_stopped

    @property
    def is_manual_takeover(self) -> bool:
        return self._manual_takeover

    def emergency_stop(self, reason: str = "User invoked emergency stop ('Shivani stop')"):
        """Immediately halts all automated operations and locks resources."""
        self._emergency_stopped = True
        for r in self.VALID_RESOURCES:
            self._locks[r] = LockHolder(
                holder_id="emergency_stop",
                priority=ActionPriority.EMERGENCY_STOP,
                reason=reason,
            )

    def reset_emergency_stop(self):
        """Clears emergency stop status."""
        self._emergency_stopped = False
        for r in self.VALID_RESOURCES:
            if self._locks[r] and self._locks[r].holder_id == "emergency_stop":
                self._locks[r] = None

    def begin_manual_takeover(self):
        """User manually takes control of computer."""
        self._manual_takeover = True
        for r in self.VALID_RESOURCES:
            self._locks[r] = LockHolder(
                holder_id="user_manual",
                priority=ActionPriority.DIRECT_USER_COMMAND,
                reason="Manual user takeover",
            )

    def end_manual_takeover(self):
        """Releases manual takeover state."""
        self._manual_takeover = False
        for r in self.VALID_RESOURCES:
            if self._locks[r] and self._locks[r].holder_id == "user_manual":
                self._locks[r] = None

    def acquire_lock(
        self,
        resource: str,
        holder_id: str,
        priority: ActionPriority,
        reason: str = "",
    ) -> bool:
        """
        Attempts to acquire a resource lock. If occupied by a lower-priority task,
        preempts it safely.
        """
        if self._emergency_stopped and priority < ActionPriority.EMERGENCY_STOP:
            return False

        if self._manual_takeover and priority < ActionPriority.DIRECT_USER_COMMAND:
            return False

        if resource not in self.VALID_RESOURCES:
            raise ValueError(f"Unknown computer resource: '{resource}'")

        current = self._locks[resource]
        if current is None:
            self._locks[resource] = LockHolder(holder_id=holder_id, priority=priority, reason=reason)
            return True

        if priority > current.priority:
            # Preempt lower priority lock
            self._locks[resource] = LockHolder(holder_id=holder_id, priority=priority, reason=reason)
            return True

        return False

    def release_lock(self, resource: str, holder_id: str) -> bool:
        """Releases lock if held by holder_id."""
        if resource not in self.VALID_RESOURCES:
            return False

        current = self._locks[resource]
        if current and current.holder_id == holder_id:
            self._locks[resource] = None
            return True
        return False

    def release_all_for_holder(self, holder_id: str):
        for r in self.VALID_RESOURCES:
            self.release_lock(r, holder_id)

    def is_locked(self, resource: str) -> bool:
        return self._locks.get(resource) is not None
