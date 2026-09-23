"""
SHIVANI Application Management Tools
Provides registered tools for opening, closing, focusing, and inspecting applications.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.application import ApplicationManager
from tools.desktop.window import WindowManager


class OpenAppArgs(BaseModel):
    app_name: str = Field(description="Name or alias of application to open (e.g. 'chrome', 'Code', 'notepad', 'calc')")
    arguments: List[str] = Field(default_factory=list, description="Command line arguments for the application")


class OpenAppTool(BaseTool):
    name = "computer.open_app"
    description = "Launch an application on the user's computer and verify process and window existence."
    permission_level = RiskLevel.SAFE
    args_schema = OpenAppArgs
    timeout = 20.0

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        super().__init__()
        self.app_manager = app_manager or ApplicationManager()

    async def run(self, app_name: str, arguments: List[str] = None) -> Dict[str, Any]:
        return await self.app_manager.open_application(app_name=app_name, arguments=arguments, timeout=self.timeout)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        proc_verified = result_data.get("process_verified", False)
        win_verified = result_data.get("window_verified", False)
        is_verified = proc_verified or win_verified
        return {
            "verified": is_verified,
            "process_verified": proc_verified,
            "window_verified": win_verified,
            "app_name": kwargs.get("app_name")
        }


class CloseAppArgs(BaseModel):
    app_name: Optional[str] = Field(default=None, description="Name or title of application to close (e.g. 'chrome', 'notepad')")
    pid: Optional[int] = Field(default=None, description="PID of process to terminate")
    force: bool = Field(default=False, description="Whether to forcefully kill the process")


class CloseAppTool(BaseTool):
    name = "computer.close_app"
    description = "Close an application gracefully or forcefully by name or PID."
    permission_level = RiskLevel.SAFE
    args_schema = CloseAppArgs
    timeout = 10.0

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        super().__init__()
        self.app_manager = app_manager or ApplicationManager()

    async def run(self, app_name: Optional[str] = None, pid: Optional[int] = None, force: bool = False) -> Dict[str, Any]:
        return await self.app_manager.close_application(app_name=app_name, pid=pid, force=force)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        still_running = result_data.get("still_running", True)
        return {
            "verified": not still_running,
            "closed": not still_running,
            "target": kwargs.get("app_name") or kwargs.get("pid")
        }


class FocusAppArgs(BaseModel):
    app_name: str = Field(description="Name or title pattern of application to bring to the foreground")


class FocusAppTool(BaseTool):
    name = "computer.focus_app"
    description = "Switch active focus to a specified application or window."
    permission_level = RiskLevel.SAFE
    args_schema = FocusAppArgs
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self, app_name: str) -> Dict[str, Any]:
        return await self.window_manager.focus_window(app_name)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        verified = result_data.get("verified", False) or result_data.get("focused", False)
        return {
            "verified": verified,
            "active_window": result_data.get("active_window_title")
        }


class ListAppsTool(BaseTool):
    name = "computer.list_apps"
    description = "Discover available and installed applications on the computer."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, app_manager: Optional[ApplicationManager] = None):
        super().__init__()
        self.app_manager = app_manager or ApplicationManager()

    async def run(self) -> List[Dict[str, str]]:
        return await self.app_manager.list_available_apps()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "count": len(result_data)}


class ActiveWindowTool(BaseTool):
    name = "computer.active_window"
    description = "Inspect the currently active foreground window, title, and process ID."
    permission_level = RiskLevel.SAFE
    timeout = 5.0

    def __init__(self, window_manager: Optional[WindowManager] = None):
        super().__init__()
        self.window_manager = window_manager or WindowManager()

    async def run(self) -> Dict[str, Any]:
        win = await self.window_manager.get_active_window()
        if not win:
            return {"window_title": "None", "pid": None, "app_name": "None", "handle": None}
        return {
            "window_title": win.title,
            "pid": win.pid,
            "app_name": win.app_name,
            "handle": win.handle,
            "rect": win.rect,
            "is_minimized": win.is_minimized,
            "is_maximized": win.is_maximized
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "title": result_data.get("window_title")}
