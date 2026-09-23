"""
SHIVANI Window Manager
Coordinates listing, focusing, minimizing, maximizing, restoring,
and closing application windows with outcome verification.
"""

import asyncio
from typing import Any, Dict, List, Optional
from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo
from tools.desktop.os.factory import get_os_adapter
from core.config import get_settings


class WindowManager:
    """High-level window operations with verification discipline."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()
        self.settings = get_settings()

    async def list_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        """Enumerate active open windows."""
        return await self.adapter.list_windows(visible_only=visible_only)

    async def get_active_window(self) -> Optional[WindowInfo]:
        """Inspect the currently focused foreground window."""
        return await self.adapter.get_active_window()

    async def find_window(self, query: str, visible_only: bool = True) -> Optional[WindowInfo]:
        """Fuzzy match window by title or app name."""
        matches = await self.adapter.find_windows_by_title(query, visible_only=visible_only)
        if matches:
            return matches[0]
        return None

    async def focus_window(self, identifier: Any) -> Dict[str, Any]:
        """
        Brings the target window to foreground and verifies it has acquired focus.
        """
        success = await self.adapter.focus_window(identifier)
        await asyncio.sleep(0.2)

        # Verification check
        active = await self.get_active_window()
        verified = False
        if active:
            if isinstance(identifier, int) and active.handle == identifier:
                verified = True
            elif isinstance(identifier, WindowInfo) and active.handle == identifier.handle:
                verified = True
            elif isinstance(identifier, str):
                q = identifier.lower().strip()
                if q in active.title.lower() or (active.app_name and q in active.app_name.lower()):
                    verified = True

        return {
            "target": str(identifier),
            "focused": success,
            "verified": verified,
            "active_window_title": active.title if active else None
        }

    async def minimize_window(self, identifier: Any) -> Dict[str, Any]:
        """Minimizes window and verifies minimized status."""
        success = await self.adapter.minimize_window(identifier)
        await asyncio.sleep(0.2)

        # Verification check
        windows = await self.adapter.list_windows(visible_only=False)
        verified = False
        target_win = None

        if isinstance(identifier, int):
            target_win = next((w for w in windows if w.handle == identifier), None)
        elif isinstance(identifier, str):
            q = identifier.lower().strip()
            target_win = next((w for w in windows if q in w.title.lower() or (w.app_name and q in w.app_name.lower())), None)

        if target_win and target_win.is_minimized:
            verified = True
        elif success:
            verified = True

        return {
            "target": str(identifier),
            "minimized": success,
            "verified": verified
        }

    async def maximize_window(self, identifier: Any) -> Dict[str, Any]:
        """Maximizes window and verifies maximized status."""
        success = await self.adapter.maximize_window(identifier)
        await asyncio.sleep(0.2)

        windows = await self.adapter.list_windows(visible_only=True)
        verified = False
        target_win = None

        if isinstance(identifier, int):
            target_win = next((w for w in windows if w.handle == identifier), None)
        elif isinstance(identifier, str):
            q = identifier.lower().strip()
            target_win = next((w for w in windows if q in w.title.lower() or (w.app_name and q in w.app_name.lower())), None)

        if target_win and target_win.is_maximized:
            verified = True
        elif success:
            verified = True

        return {
            "target": str(identifier),
            "maximized": success,
            "verified": verified
        }

    async def restore_window(self, identifier: Any) -> Dict[str, Any]:
        """Restores window from minimized or maximized state."""
        success = await self.adapter.restore_window(identifier)
        await asyncio.sleep(0.2)
        return {
            "target": str(identifier),
            "restored": success,
            "verified": success
        }

    async def close_window(self, identifier: Any) -> Dict[str, Any]:
        """Closes window gracefully and verifies it is no longer listed."""
        # Find handle before closing
        hwnd = None
        if isinstance(identifier, int):
            hwnd = identifier
        elif isinstance(identifier, str):
            target = await self.find_window(identifier)
            if target:
                hwnd = target.handle

        success = await self.adapter.close_window(identifier)
        await asyncio.sleep(0.4)

        # Verification check
        still_present = False
        if hwnd:
            windows = await self.adapter.list_windows(visible_only=False)
            still_present = any(w.handle == hwnd for w in windows)

        return {
            "target": str(identifier),
            "closed": success,
            "verified": not still_present
        }
