"""
SHIVANI Windows Application Adapter
Controls native Windows desktop software with process lifecycle management
and visual/GUI fallback integration.
"""

import asyncio
import logging
import os
import subprocess
from typing import Any, Dict, Optional

from adapters.base import AppAdapter, AppInfo
from adapters.discovery import AppDiscovery

logger = logging.getLogger("shivani.adapters.windows")


class WindowsAppAdapter(AppAdapter):
    """Adapter for interacting with Windows desktop applications."""

    def __init__(self, app_name: str, executable_path: Optional[str] = None):
        self.name = app_name
        self.app_type = "desktop"
        super().__init__()
        self._executable_path = executable_path
        self._process: Optional[subprocess.Popen] = None
        self._discovery = AppDiscovery()

    async def is_available(self) -> bool:
        if self._executable_path and os.path.exists(self._executable_path):
            return True
        info = self._discovery.find_app(self.name)
        if info and info.executable_path:
            self._executable_path = info.executable_path
            return True
        return False

    async def launch(self, **kwargs: Any) -> bool:
        if not await self.is_available():
            logger.warning(f"Cannot launch '{self.name}': application not found on host.")
            return False

        args = kwargs.get("args", [])
        try:
            cmd = [self._executable_path] + args if self._executable_path else [self.name]
            self._process = subprocess.Popen(
                cmd,
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Launched Windows app '{self.name}' (PID: {self._process.pid})")
            return True
        except Exception as e:
            logger.error(f"Failed to launch '{self.name}': {e}")
            return False

    async def close(self) -> bool:
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                await asyncio.sleep(0.5)
                if self._process.poll() is None:
                    self._process.kill()
                logger.info(f"Closed application '{self.name}'")
                return True
            except Exception as e:
                logger.warning(f"Error terminating process for '{self.name}': {e}")

        # Fallback to taskkill if process handle lost
        if os.name == "nt":
            try:
                exe_name = os.path.basename(self._executable_path) if self._executable_path else f"{self.name}.exe"
                res = subprocess.run(["taskkill", "/F", "/IM", exe_name], capture_output=True)
                return res.returncode == 0
            except Exception:
                pass
        return False

    async def execute_action(self, action: str, **kwargs: Any) -> Any:
        if action == "launch":
            return await self.launch(**kwargs)
        elif action in ("close", "terminate", "exit"):
            return await self.close()
        elif action == "status":
            return await self.get_state()
        else:
            # Fallback to general GUI control / vision
            return {"status": "unsupported_native_action", "action": action, "fallback": "gui_input"}

    async def get_state(self) -> Dict[str, Any]:
        is_running = False
        if self._process and self._process.poll() is None:
            is_running = True
        return {
            "name": self.name,
            "executable": self._executable_path,
            "is_running": is_running,
            "pid": self._process.pid if (self._process and is_running) else None,
        }
