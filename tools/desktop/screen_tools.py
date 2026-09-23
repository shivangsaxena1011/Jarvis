"""
SHIVANI Screenshot & Display Capture Tools
Provides registered tools for capturing full-screen, active window,
and regional screenshots with secure disk storage and outcome verification.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.screen import ScreenCapture


class ScreenshotArgs(BaseModel):
    filename: Optional[str] = Field(default=None, description="Optional custom filename for the screenshot")
    active_window_only: bool = Field(default=False, description="Capture only the currently focused foreground window")
    region: Optional[Dict[str, int]] = Field(default=None, description="Optional bounding box {'left': x, 'top': y, 'width': w, 'height': h}")


class ScreenshotTool(BaseTool):
    name = "computer.screenshot"
    description = "Capture an image of the full desktop, active window, or region for visual observation."
    permission_level = RiskLevel.SAFE
    args_schema = ScreenshotArgs
    timeout = 10.0

    def __init__(self, screen_capture: Optional[ScreenCapture] = None):
        super().__init__()
        self.screen_capture = screen_capture or ScreenCapture()

    async def run(
        self,
        filename: Optional[str] = None,
        active_window_only: bool = False,
        region: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        if active_window_only:
            return await self.screen_capture.capture_active_window(filename=filename)
        return await self.screen_capture.capture(filename=filename, region=region)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        from pathlib import Path
        path = Path(result_data.get("path", ""))
        exists = path.exists() and path.stat().st_size > 0
        return {
            "verified": exists,
            "path": str(path),
            "size_bytes": path.stat().st_size if exists else 0
        }
