"""
SHIVANI Browser Agent Stub (Phase 4 Preparation)
Provides an interface and detection mechanisms for desktop browsers:
Google Chrome, Brave, Microsoft Edge, and Mozilla Firefox.
"""

from typing import Any, Dict, List, Optional, Tuple
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter


class BrowserAgent:
    """Precursor interface to Phase 4 dedicated Browser Agent."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()

    async def detect_installed_browsers(self) -> Dict[str, Optional[str]]:
        """
        Detects which supported browsers are installed on the local system.
        Checks Chrome, Brave, Edge, and Firefox.
        """
        browsers = {
            "chrome": ["chrome", "google chrome"],
            "brave": ["brave", "brave browser"],
            "edge": ["msedge", "edge", "microsoft edge"],
            "firefox": ["firefox", "mozilla firefox"],
        }
        detected = {}

        for browser_id, aliases in browsers.items():
            path = None
            for alias in aliases:
                resolved = await self.adapter.resolve_app_path(alias)
                if resolved:
                    path = resolved
                    break
            detected[browser_id] = path

        return detected

    async def is_browser_active(self) -> Tuple[bool, str]:
        """Checks if any supported browser currently holds foreground focus."""
        active = await self.adapter.get_active_window()
        if not active or not active.title:
            return False, ""

        title_lower = active.title.lower()
        app_lower = (active.app_name or "").lower()

        for b in ["chrome", "edge", "brave", "firefox"]:
            if b in title_lower or b in app_lower:
                return True, b

        return False, ""
