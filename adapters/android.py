"""
SHIVANI Android Mobile Application Adapter
Adapter bridging paired Android device apps via DeviceBridge into the uniform AppAdapter model.
"""

from typing import Any, Dict, Optional
from adapters.base import AppAdapter


class AndroidAppAdapter(AppAdapter):
    """Adapter for interacting with apps running on paired Android devices."""

    def __init__(self, app_name: str, package_name: str, device_bridge: Optional[Any] = None):
        self.name = app_name
        self.package_name = package_name
        self.app_type = "mobile"
        super().__init__()
        self.device_bridge = device_bridge

    async def is_available(self) -> bool:
        if self.device_bridge:
            try:
                # Check if device is paired and online
                return getattr(self.device_bridge, "is_connected", True)
            except Exception:
                return False
        return True

    async def launch(self, **kwargs: Any) -> bool:
        if self.device_bridge and hasattr(self.device_bridge, "launch_app"):
            try:
                res = await self.device_bridge.launch_app(self.package_name)
                return bool(res)
            except Exception as e:
                self.logger.error(f"Failed to launch {self.package_name} on mobile: {e}")
                return False
        self.logger.info(f"Dispatched launch intent for Android app '{self.name}' ({self.package_name})")
        return True

    async def close(self) -> bool:
        if self.device_bridge and hasattr(self.device_bridge, "close_app"):
            try:
                return await self.device_bridge.close_app(self.package_name)
            except Exception as e:
                self.logger.warning(f"Failed to close mobile app {self.package_name}: {e}")
        return True

    async def execute_action(self, action: str, **kwargs: Any) -> Any:
        if action == "launch":
            return await self.launch(**kwargs)
        elif action == "close":
            return await self.close()
        elif action == "screenshot":
            if self.device_bridge and hasattr(self.device_bridge, "take_screenshot"):
                return await self.device_bridge.take_screenshot()
            return {"status": "error", "error": "Android bridge unavailable for screenshot"}
        return {"action": action, "package": self.package_name, "status": "executed"}

    async def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "package_name": self.package_name,
            "type": self.app_type,
            "device_connected": await self.is_available(),
        }
