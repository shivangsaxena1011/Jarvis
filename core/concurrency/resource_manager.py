"""
SHIVANI Resource Manager
Provides fine-grained concurrency control and mutual exclusion locks for:
- Local file paths (prevents concurrent write collisions)
- Git repositories (prevents conflicting branches/commits)
- Mobile devices and bridges (prevents conflicting ADB/touch commands)
- Browser sessions (prevents concurrent tab/navigation conflicts)
"""

import asyncio
from contextlib import asynccontextmanager
import os
import time
from typing import Any, AsyncIterator, Dict, Optional, Set


class LockAcquisitionTimeout(Exception):
    """Raised when a resource lock cannot be acquired within the timeout period."""
    pass


class ResourceLock:
    def __init__(self, resource_id: str):
        self.resource_id = resource_id
        self._lock = asyncio.Lock()
        self.holder: Optional[str] = None
        self.acquired_at: Optional[float] = None

    @property
    def is_locked(self) -> bool:
        return self._lock.locked()

    async def acquire(self, holder: str, timeout: float = 10.0) -> bool:
        try:
            await asyncio.wait_for(self._lock.acquire(), timeout=timeout)
            self.holder = holder
            self.acquired_at = time.time()
            return True
        except asyncio.TimeoutError:
            raise LockAcquisitionTimeout(
                f"Timed out acquiring lock on '{self.resource_id}' held by '{self.holder}'"
            )

    def release(self) -> None:
        if self._lock.locked():
            self._lock.release()
            self.holder = None
            self.acquired_at = None


class ResourceManager:
    def __init__(self):
        self._locks: Dict[str, ResourceLock] = {}
        self._global_lock = asyncio.Lock()

    async def _get_or_create_lock(self, key: str) -> ResourceLock:
        async with self._global_lock:
            if key not in self._locks:
                self._locks[key] = ResourceLock(key)
            return self._locks[key]

    @asynccontextmanager
    async def lock_file(self, file_path: str, holder: str = "agent", timeout: float = 10.0) -> AsyncIterator[None]:
        norm_path = os.path.normpath(os.path.abspath(file_path))
        key = f"file:{norm_path}"
        lock = await self._get_or_create_lock(key)
        await lock.acquire(holder=holder, timeout=timeout)
        try:
            yield
        finally:
            lock.release()

    @asynccontextmanager
    async def lock_repository(self, repo_path: str, holder: str = "coding_agent", timeout: float = 15.0) -> AsyncIterator[None]:
        norm_path = os.path.normpath(os.path.abspath(repo_path))
        key = f"repo:{norm_path}"
        lock = await self._get_or_create_lock(key)
        await lock.acquire(holder=holder, timeout=timeout)
        try:
            yield
        finally:
            lock.release()

    @asynccontextmanager
    async def lock_device(self, device_id: str, holder: str = "phone_agent", timeout: float = 10.0) -> AsyncIterator[None]:
        key = f"device:{device_id}"
        lock = await self._get_or_create_lock(key)
        await lock.acquire(holder=holder, timeout=timeout)
        try:
            yield
        finally:
            lock.release()

    @asynccontextmanager
    async def lock_browser(self, session_id: str = "default", holder: str = "browser_agent", timeout: float = 10.0) -> AsyncIterator[None]:
        key = f"browser:{session_id}"
        lock = await self._get_or_create_lock(key)
        await lock.acquire(holder=holder, timeout=timeout)
        try:
            yield
        finally:
            lock.release()

    def is_locked(self, resource_type: str, target: str) -> bool:
        if resource_type in ("file", "repo"):
            target = os.path.normpath(os.path.abspath(target))
        key = f"{resource_type}:{target}"
        lock = self._locks.get(key)
        return lock.is_locked if lock else False

    def get_lock_info(self, resource_type: str, target: str) -> Optional[Dict[str, Any]]:
        if resource_type in ("file", "repo"):
            target = os.path.normpath(os.path.abspath(target))
        key = f"{resource_type}:{target}"
        lock = self._locks.get(key)
        if not lock or not lock.is_locked:
            return None
        return {
            "resource_id": lock.resource_id,
            "holder": lock.holder,
            "acquired_at": lock.acquired_at,
            "age_seconds": round(time.time() - (lock.acquired_at or time.time()), 2),
        }
