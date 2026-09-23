"""
SHIVANI Screen Capture Manager
Coordinates full-screen, window-specific, and regional screenshot captures.
Ensures temporary screenshots are managed cleanly.
"""

import time
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter
from core.config import get_settings


class ScreenCapture:
    """Manages screenshot acquisition for observation and vision feeds."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()
        self.settings = get_settings()

    async def capture(
        self,
        filename: Optional[str] = None,
        region: Optional[Dict[str, int]] = None,
        window_handle: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Captures screenshot and stores in the configured screenshot directory.
        """
        dest_dir = self.settings.screenshot_path
        timestamp_ms = int(time.time() * 1000)
        file_name = filename or f"screenshot_{timestamp_ms}.png"
        target_path = dest_dir / file_name

        result = await self.adapter.capture_screen(
            output_path=target_path,
            region=region,
            window_handle=window_handle
        )

        return {
            "path": result["path"],
            "filename": file_name,
            "width": result["width"],
            "height": result["height"],
            "size_bytes": result["size_bytes"],
            "timestamp": timestamp_ms,
            "region": region,
            "window_handle": window_handle
        }

    async def capture_active_window(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """Captures only the bounding region of the currently active window."""
        active = await self.adapter.get_active_window()
        handle = active.handle if active else None
        return await self.capture(filename=filename, window_handle=handle)
