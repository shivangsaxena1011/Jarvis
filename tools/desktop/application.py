"""
SHIVANI Desktop Application Manager
Coordinates application discovery, launch, process verification,
window appearance verification, responsiveness checks, and termination.
"""

import os
import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional
import psutil

from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo
from tools.desktop.os.factory import get_os_adapter
from core.config import get_settings

try:
    import win32gui
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False


class ApplicationManager:
    """Manages application lifecycle on the host OS with strict verification discipline."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()
        self.settings = get_settings()

    async def open_application(
        self,
        app_name: str,
        arguments: Optional[List[str]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Locates executable, launches process, and verifies process + window appearance.
        """
        max_timeout = timeout or self.settings.DESKTOP_APP_TIMEOUT
        retries = self.settings.DESKTOP_MAX_RETRIES
        last_error = None

        # 1. Resolve application executable path
        resolved_path = await self.adapter.resolve_app_path(app_name)
        if not resolved_path:
            raise FileNotFoundError(
                f"Application '{app_name}' could not be located on this system. "
                "Checked known paths, Windows registry App Paths, Start Menu, and PATH."
            )

        # 2. Launch process with retry capability
        launch_result = None
        for attempt in range(1, retries + 1):
            try:
                launch_result = await self.adapter.launch_app(resolved_path, arguments)
                break
            except Exception as e:
                last_error = str(e)
                if attempt < retries:
                    await asyncio.sleep(0.5 * attempt)

        if not launch_result:
            raise RuntimeError(f"Failed to launch '{app_name}' after {retries} attempts: {last_error}")

        pid = launch_result.get("pid")
        clean_target = Path(app_name).stem.lower()

        # 3. VERIFICATION: Wait for process and visible window appearance
        poll_interval = 0.4
        elapsed = 0.0
        process_found = False
        window_found = False
        detected_window: Optional[WindowInfo] = None

        while elapsed < max_timeout:
            # Check process presence
            if not process_found:
                if hasattr(self.adapter, "launched_processes"):
                    for lp in getattr(self.adapter, "launched_processes", []):
                        if (pid and lp.get("pid") == pid) or clean_target in str(lp.get("executable", "")).lower():
                            process_found = True
                            break

                if not process_found:
                    for proc in psutil.process_iter(["pid", "name"]):
                        try:
                            pname = (proc.info["name"] or "").lower()
                            if clean_target in pname or (pid and proc.info["pid"] == pid):
                                process_found = True
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

            # Check window appearance
            windows = await self.adapter.list_windows(visible_only=True)
            for w in windows:
                if clean_target in w.title.lower() or (w.app_name and clean_target in w.app_name.lower()):
                    window_found = True
                    detected_window = w
                    break

            if process_found and window_found:
                break

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        # Check responsiveness if window found
        is_responsive = True
        if detected_window and HAS_WIN32 and detected_window.handle:
            try:
                is_hung = win32gui.IsHungAppWindow(detected_window.handle)
                is_responsive = not is_hung
            except Exception:
                pass

        return {
            "app_name": app_name,
            "resolved_path": resolved_path,
            "pid": pid,
            "process_verified": process_found,
            "window_verified": window_found,
            "window_title": detected_window.title if detected_window else None,
            "is_responsive": is_responsive,
            "launch_duration_sec": round(elapsed, 2),
            "status": "success" if (process_found or window_found) else "unverified"
        }

    async def close_application(
        self,
        app_name: Optional[str] = None,
        pid: Optional[int] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """Closes application by terminating its process or closing its windows."""
        if not app_name and not pid:
            raise ValueError("Must specify either app_name or pid to close.")

        terminated_count = 0
        clean_target = Path(app_name).stem.lower() if app_name else None

        # Terminate simulated processes if mock adapter
        if hasattr(self.adapter, "launched_processes"):
            procs = getattr(self.adapter, "launched_processes", [])
            to_remove = [p for p in procs if (pid and p.get("pid") == pid) or (clean_target and clean_target in str(p.get("executable", "")).lower())]
            for r in to_remove:
                procs.remove(r)
                terminated_count += 1

        # Terminate processes
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                match = False
                if pid and proc.info["pid"] == pid:
                    match = True
                elif clean_target and clean_target in (proc.info["name"] or "").lower():
                    match = True

                if match:
                    if force:
                        proc.kill()
                    else:
                        proc.terminate()
                    terminated_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        await asyncio.sleep(0.4)

        # Verification check
        still_running = False
        if hasattr(self.adapter, "launched_processes"):
            for lp in getattr(self.adapter, "launched_processes", []):
                if (pid and lp.get("pid") == pid) or (clean_target and clean_target in str(lp.get("executable", "")).lower()):
                    still_running = True
                    break
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if pid and proc.info["pid"] == pid:
                    still_running = True
                    break
                elif clean_target and clean_target in (proc.info["name"] or "").lower():
                    still_running = True
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return {
            "target": app_name or pid,
            "terminated_count": terminated_count,
            "still_running": still_running,
            "verified": not still_running
        }

    async def list_available_apps(self) -> List[Dict[str, str]]:
        """Returns discovered installed applications."""
        return await self.adapter.list_installed_apps()
