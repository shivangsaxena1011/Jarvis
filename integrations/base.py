"""
SHIVANI Base Integration Interface
Provides unified rate-limiting, account context, error masking, and safety contracts.
"""

import time
import asyncio
from abc import ABC
from typing import Any, Dict, Optional
from core.config import get_settings


class BaseIntegration(ABC):
    """Base class for all SHIVANI third-party service integrations."""

    def __init__(self, name: str):
        self.name = name
        self.settings = get_settings()
        self.cooldown_seconds = self.settings.RATE_LIMIT_COOLDOWN_SECONDS
        self._last_call_timestamp: float = 0.0
        self._active_account: Optional[str] = None

    async def enforce_rate_limit(self) -> None:
        """Enforces per-service rate-limiting cooldown to respect platform thresholds."""
        now = time.time()
        elapsed = now - self._last_call_timestamp
        if elapsed < self.cooldown_seconds:
            await asyncio.sleep(self.cooldown_seconds - elapsed)
        self._last_call_timestamp = time.time()

    def set_active_account(self, account_identifier: str) -> None:
        self._active_account = account_identifier

    def get_active_account(self) -> Optional[str]:
        return self._active_account
