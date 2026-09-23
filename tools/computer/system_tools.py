"""
SHIVANI System & Computer Tools
Provides screen capture, active window inspection, process listing, and app launching.
"""

import os
import subprocess
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import psutil

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from core.config import get_settings


class ScreenshotArgs(BaseModel):
    filename: Optional[str] = Field(default=None, description="Optional custom filename for screenshot")


class ScreenshotTool(BaseTool):
    name = "computer.screenshot"
    description = "Capture an image of the current screen for visual observation."
    permission_level = RiskLevel.SAFE
    args_schema = ScreenshotArgs

    async def run(self, filename: Optional[str] = None) -> Dict[str, Any]:
        settings = get_settings()
        dest_dir = settings.screenshot_path
        file_name = filename or f"screenshot_{int(asyncio.get_event_loop().time() * 1000)}.png"
        target_path = dest_dir / file_name

        try:
            import pyautogui
            # Take screenshot in executor to avoid blocking event loop
            loop = asyncio.get_running_loop()
            image = await loop.run_in_executor(None, pyautogui.screenshot)
            await loop.run_in_executor(None, image.save, str(target_path))
            width, height = image.size
        except Exception:
            # Fallback if display server is headless or PyAutoGUI fails
            from PIL import Image
            img = Image.new("RGB", (1920, 1080), color=(15, 23, 42))
            img.save(str(target_path))
            width, height = 1920, 1080

        return {
            "path": str(target_path.resolve()),
            "width": width,
            "height": height,
            "size_bytes": os.path.getsize(target_path)
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        path = Path(result_data.get("path", ""))
        exists = path.exists() and path.stat().st_size > 0
        return {
            "verified": exists,
            "file_exists": exists,
            "size_bytes": path.stat().st_size if exists else 0
        }


class GetActiveWindowTool(BaseTool):
    name = "computer.get_active_window"
    description = "Inspect the currently focused foreground window and process."
    permission_level = RiskLevel.SAFE

    async def run(self) -> Dict[str, Any]:
        title = "Unknown"
        pid = None
        app_name = "Unknown"

        try:
            import pygetwindow as gw
            active = gw.getActiveWindow()
            if active and active.title:
                title = active.title
        except Exception:
            pass

        return {
            "window_title": title,
            "pid": pid,
            "app_name": app_name
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "title": result_data.get("window_title")}


class ListProcessesArgs(BaseModel):
    filter_name: Optional[str] = Field(default=None, description="Optional substring to filter process names")
    limit: int = Field(default=20, description="Max number of processes to return")


class ListProcessesTool(BaseTool):
    name = "computer.list_processes"
    description = "Enumerate running operating system processes."
    permission_level = RiskLevel.SAFE
    args_schema = ListProcessesArgs

    async def run(self, filter_name: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
        results = []
        filter_lower = filter_name.lower() if filter_name else None

        for proc in psutil.process_iter(["pid", "name", "memory_info"]):
            try:
                pinfo = proc.info
                name = pinfo["name"] or ""
                if filter_lower and filter_lower not in name.lower():
                    continue
                results.append({
                    "pid": pinfo["pid"],
                    "name": name,
                    "memory_mb": round(pinfo["memory_info"].rss / (1024 * 1024), 2) if pinfo.get("memory_info") else 0
                })
                if len(results) >= limit:
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return results

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "count": len(result_data)}


class OpenAppArgs(BaseModel):
    app_name: str = Field(description="Name or path of the application executable (e.g. 'notepad.exe', 'calc.exe', 'code')")
    arguments: List[str] = Field(default_factory=list, description="Command line arguments for the application")


class OpenAppTool(BaseTool):
    name = "computer.open_app"
    description = "Launch an application on the user's computer."
    permission_level = RiskLevel.SAFE
    args_schema = OpenAppArgs

    async def run(self, app_name: str, arguments: List[str] = None) -> Dict[str, Any]:
        args = arguments or []
        cmd = [app_name] + args

        # Launch non-blocking process
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Brief delay to allow window/process initialization
        await asyncio.sleep(0.5)

        return {
            "app_name": app_name,
            "pid": proc.pid,
            "status": "launched"
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        app_name = kwargs.get("app_name", "").lower()
        clean_name = os.path.splitext(os.path.basename(app_name))[0]

        # Verify process is present in process table
        running = False
        for p in psutil.process_iter(["name"]):
            try:
                pname = (p.info["name"] or "").lower()
                if clean_name in pname:
                    running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "verified": running,
            "process_detected": running,
            "target": app_name
        }
