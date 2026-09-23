"""
SHIVANI Window Management Tools
Provides registered tools for window.list, window.focus, window.minimize,
window.maximize, window.restore, and window.close.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.window import WindowManager


class WindowIdentifierArgs(BaseModel):
    title_or_handle: Optional[str] = Field(
        default=None,
        description="Window title, app name, or window handle. If omitted, targets currently active window."
    )


class ListWindowsArgs(BaseModel):
    visible_only: bool = Field(default=True, description="Filter only windows that are currently visible")


class WindowListTool(BaseTool):
    name = "window.list"
    description = "Enumerate open application windows with titles, visibility, and state."
    permission_level = RiskLevel.SAFE
    args_schema = ListWindowsArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, visible_only: bool = True) -> List[Dict[str, Any]]:
        windows = await self.window_manager.list_windows(visible_only=visible_only)
        return [w.model_dump() for w in windows]

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "count": len(result_data)}


class WindowFocusTool(BaseTool):
    name = "window.focus"
    description = "Bring a window to the foreground and activate it."
    permission_level = RiskLevel.SAFE
    args_schema = WindowIdentifierArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, title_or_handle: Optional[str] = None) -> Dict[str, Any]:
        target = title_or_handle
        if not target:
            active = await self.window_manager.get_active_window()
            if not active:
                raise RuntimeError("No active window to focus.")
            target = active.handle

        return await self.window_manager.focus_window(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) or result_data.get("focused", False)}


class WindowMinimizeTool(BaseTool):
    name = "window.minimize"
    description = "Minimize an open window. If no window is specified, minimizes the current foreground window."
    permission_level = RiskLevel.SAFE
    args_schema = WindowIdentifierArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, title_or_handle: Optional[str] = None) -> Dict[str, Any]:
        target = title_or_handle
        if not target:
            active = await self.window_manager.get_active_window()
            if not active:
                raise RuntimeError("No active window to minimize.")
            target = active.handle

        return await self.window_manager.minimize_window(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) or result_data.get("minimized", False)}


class WindowMaximizeTool(BaseTool):
    name = "window.maximize"
    description = "Maximize a window to fill the screen."
    permission_level = RiskLevel.SAFE
    args_schema = WindowIdentifierArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, title_or_handle: Optional[str] = None) -> Dict[str, Any]:
        target = title_or_handle
        if not target:
            active = await self.window_manager.get_active_window()
            if not active:
                raise RuntimeError("No active window to maximize.")
            target = active.handle

        return await self.window_manager.maximize_window(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) or result_data.get("maximized", False)}


class WindowRestoreTool(BaseTool):
    name = "window.restore"
    description = "Restore a minimized or maximized window to its normal geometry."
    permission_level = RiskLevel.SAFE
    args_schema = WindowIdentifierArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, title_or_handle: Optional[str] = None) -> Dict[str, Any]:
        target = title_or_handle
        if not target:
            active = await self.window_manager.get_active_window()
            if not active:
                raise RuntimeError("No active window to restore.")
            target = active.handle

        return await self.window_manager.restore_window(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) or result_data.get("restored", False)}


class WindowCloseTool(BaseTool):
    name = "window.close"
    description = "Close a window gracefully. If no window specified, closes the current foreground window."
    permission_level = RiskLevel.SAFE
    args_schema = WindowIdentifierArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, title_or_handle: Optional[str] = None) -> Dict[str, Any]:
        target = title_or_handle
        if not target:
            active = await self.window_manager.get_active_window()
            if not active:
                raise RuntimeError("No active window to close.")
            target = active.handle

        return await self.window_manager.close_window(target)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) or result_data.get("closed", False)}
