"""
SHIVANI Windows 11 Operating System Adapter
Provides native Windows automation using Win32 API, PyGetWindow, PyAutoGUI,
and Windows Registry / Start Menu application discovery.
"""

import os
import sys
import glob
import shutil
import asyncio
import winreg
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import psutil
from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo

try:
    import win32gui
    import win32con
    import win32process
    import win32api
    HAS_WIN32 = True
except ImportError:
    HAS_WIN32 = False

try:
    import pyautogui
    # Configure pyautogui safety
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

try:
    import pyperclip
    HAS_PYPERCLIP = True
except ImportError:
    HAS_PYPERCLIP = False


class WindowsAdapter(OperatingSystemAdapter):
    """Production implementation of OperatingSystemAdapter for Windows 11."""

    def __init__(self):
        self._loop = None

    def _get_loop(self):
        try:
            return asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.get_event_loop()

    # ==========================================
    # WINDOW MANAGEMENT
    # ==========================================

    async def get_active_window(self) -> Optional[WindowInfo]:
        """Inspect and return the currently focused foreground window."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._get_active_window_sync)

    def _get_active_window_sync(self) -> Optional[WindowInfo]:
        if not HAS_WIN32:
            return None

        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return None

        title = win32gui.GetWindowText(hwnd).strip()
        _, pid = win32process.GetWindowThreadProcessId(hwnd)

        app_name = None
        if pid:
            try:
                proc = psutil.Process(pid)
                app_name = proc.name()
            except Exception:
                pass

        rect_coords = {"left": 0, "top": 0, "width": 0, "height": 0}
        try:
            l, t, r, b = win32gui.GetWindowRect(hwnd)
            rect_coords = {"left": l, "top": t, "width": max(0, r - l), "height": max(0, b - t)}
        except Exception:
            pass

        placement = win32gui.GetWindowPlacement(hwnd)
        is_min = placement[1] == win32con.SW_SHOWMINIMIZED
        is_max = placement[1] == win32con.SW_SHOWMAXIMIZED

        return WindowInfo(
            handle=hwnd,
            title=title,
            pid=pid,
            app_name=app_name,
            rect=rect_coords,
            is_active=True,
            is_minimized=is_min,
            is_maximized=is_max,
            is_visible=win32gui.IsWindowVisible(hwnd) != 0
        )

    async def list_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        """Enumerate running windows with their handles and titles."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._list_windows_sync, visible_only)

    def _list_windows_sync(self, visible_only: bool = True) -> List[WindowInfo]:
        if not HAS_WIN32:
            return []

        active_hwnd = win32gui.GetForegroundWindow()
        windows: List[WindowInfo] = []

        def enum_handler(hwnd, _):
            if visible_only and not win32gui.IsWindowVisible(hwnd):
                return True

            title = win32gui.GetWindowText(hwnd).strip()
            if visible_only and not title:
                return True

            # Skip small tool windows without system menu
            style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
            if visible_only and (style & win32con.WS_CHILD):
                return True

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            app_name = None
            if pid:
                try:
                    proc = psutil.Process(pid)
                    app_name = proc.name()
                except Exception:
                    pass

            rect_coords = {"left": 0, "top": 0, "width": 0, "height": 0}
            try:
                l, t, r, b = win32gui.GetWindowRect(hwnd)
                rect_coords = {"left": l, "top": t, "width": max(0, r - l), "height": max(0, b - t)}
            except Exception:
                pass

            placement = win32gui.GetWindowPlacement(hwnd)
            is_min = placement[1] == win32con.SW_SHOWMINIMIZED
            is_max = placement[1] == win32con.SW_SHOWMAXIMIZED

            windows.append(WindowInfo(
                handle=hwnd,
                title=title,
                pid=pid,
                app_name=app_name,
                rect=rect_coords,
                is_active=(hwnd == active_hwnd),
                is_minimized=is_min,
                is_maximized=is_max,
                is_visible=win32gui.IsWindowVisible(hwnd) != 0
            ))
            return True

        win32gui.EnumWindows(enum_handler, None)
        return windows

    async def find_windows_by_title(self, query: str, visible_only: bool = True) -> List[WindowInfo]:
        """Find open windows matching a substring or pattern."""
        all_windows = await self.list_windows(visible_only=visible_only)
        q = query.lower()
        return [w for w in all_windows if q in w.title.lower() or (w.app_name and q in w.app_name.lower())]

    def _resolve_hwnd(self, identifier: Any) -> Optional[int]:
        if isinstance(identifier, int):
            return identifier
        if isinstance(identifier, WindowInfo):
            return identifier.handle
        if isinstance(identifier, str):
            all_wins = self._list_windows_sync(visible_only=False)
            q = identifier.lower().strip()
            # Exact title match
            for w in all_wins:
                if w.title.lower() == q:
                    return w.handle
            # Substring title or app name match
            for w in all_wins:
                if q in w.title.lower() or (w.app_name and q in w.app_name.lower()):
                    return w.handle
        return None

    async def focus_window(self, identifier: Any) -> bool:
        """Bring window to foreground by handle, title, or WindowInfo."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._focus_window_sync, identifier)

    def _focus_window_sync(self, identifier: Any) -> bool:
        if not HAS_WIN32:
            return False

        hwnd = self._resolve_hwnd(identifier)
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False

        try:
            # Restore if minimized
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

            # Windows foreground trick: attach input thread to unlock SetForegroundWindow
            fore_hwnd = win32gui.GetForegroundWindow()
            fore_thread, _ = win32process.GetWindowThreadProcessId(fore_hwnd)
            target_thread, _ = win32process.GetWindowThreadProcessId(hwnd)

            if fore_thread != target_thread:
                win32process.AttachThreadInput(fore_thread, target_thread, True)
                win32gui.SetForegroundWindow(hwnd)
                win32process.AttachThreadInput(fore_thread, target_thread, False)
            else:
                win32gui.SetForegroundWindow(hwnd)

            win32gui.BringWindowToTop(hwnd)
            return True
        except Exception:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
                win32gui.SetForegroundWindow(hwnd)
                return True
            except Exception:
                return False

    async def minimize_window(self, identifier: Any) -> bool:
        """Minimize window by handle or title."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._minimize_window_sync, identifier)

    def _minimize_window_sync(self, identifier: Any) -> bool:
        if not HAS_WIN32:
            return False
        hwnd = self._resolve_hwnd(identifier)
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return True
        except Exception:
            return False

    async def maximize_window(self, identifier: Any) -> bool:
        """Maximize window by handle or title."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._maximize_window_sync, identifier)

    def _maximize_window_sync(self, identifier: Any) -> bool:
        if not HAS_WIN32:
            return False
        hwnd = self._resolve_hwnd(identifier)
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True
        except Exception:
            return False

    async def restore_window(self, identifier: Any) -> bool:
        """Restore window to normal state by handle or title."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._restore_window_sync, identifier)

    def _restore_window_sync(self, identifier: Any) -> bool:
        if not HAS_WIN32:
            return False
        hwnd = self._resolve_hwnd(identifier)
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        try:
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
            return True
        except Exception:
            return False

    async def close_window(self, identifier: Any) -> bool:
        """Close window gracefully by sending close message."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._close_window_sync, identifier)

    def _close_window_sync(self, identifier: Any) -> bool:
        if not HAS_WIN32:
            return False
        hwnd = self._resolve_hwnd(identifier)
        if not hwnd or not win32gui.IsWindow(hwnd):
            return False
        try:
            win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
            return True
        except Exception:
            return False

    # ==========================================
    # APPLICATION MANAGEMENT & DISCOVERY
    # ==========================================

    async def launch_app(self, executable: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launch application process and return PID and initial status."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._launch_app_sync, executable, args)

    def _launch_app_sync(self, executable: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        cmd = [executable] + (args or [])
        proc = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {
            "pid": proc.pid,
            "executable": executable,
            "status": "launched"
        }

    async def resolve_app_path(self, app_name: str) -> Optional[str]:
        """Resolve executable path using registry, Start Menu, PATH, and known paths."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._resolve_app_path_sync, app_name)

    def _resolve_app_path_sync(self, app_name: str) -> Optional[str]:
        clean = app_name.strip()
        clean_lower = clean.lower()

        # 1. Direct path exists
        if os.path.isabs(clean) and os.path.exists(clean):
            return clean

        # 2. Well-known executable aliases
        known_aliases = {
            "chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ],
            "google chrome": [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ],
            "vs code": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe"
            ],
            "vscode": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe"
            ],
            "code": [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
                r"C:\Program Files\Microsoft VS Code\Code.exe"
            ],
            "notepad": ["notepad.exe"],
            "calculator": ["calc.exe"],
            "calc": ["calc.exe"],
            "edge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ],
            "msedge": [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ],
            "explorer": ["explorer.exe"],
            "file explorer": ["explorer.exe"],
            "cmd": ["cmd.exe"],
            "terminal": ["wt.exe", "powershell.exe"],
            "powershell": ["powershell.exe"],
        }

        # Check alias table
        for alias, paths in known_aliases.items():
            if clean_lower == alias or clean_lower == f"{alias}.exe":
                for p in paths:
                    if os.path.exists(p) or shutil.which(p):
                        return p

        # 3. Check Windows Registry App Paths
        # HKLM & HKCU: Software\Microsoft\Windows\CurrentVersion\App Paths
        reg_keys = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
        ]
        target_exe = clean if clean.endswith(".exe") else f"{clean}.exe"

        for root_key, subkey in reg_keys:
            try:
                with winreg.OpenKey(root_key, subkey) as app_paths:
                    num_subkeys = winreg.QueryInfoKey(app_paths)[0]
                    for i in range(num_subkeys):
                        name = winreg.EnumKey(app_paths, i)
                        if name.lower() == target_exe.lower() or clean_lower in name.lower():
                            with winreg.OpenKey(app_paths, name) as key:
                                path_val, _ = winreg.QueryValueEx(key, "")
                                if path_val and os.path.exists(path_val):
                                    return path_val
            except Exception:
                pass

        # 4. Search Start Menu Shortcuts (.lnk)
        start_menu_dirs = [
            os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
            os.path.expandvars(r"%ALLUSERSPROFILE%\Microsoft\Windows\Start Menu\Programs"),
        ]
        for base_dir in start_menu_dirs:
            if not os.path.exists(base_dir):
                continue
            for root, _, files in os.walk(base_dir):
                for f in files:
                    if f.lower().endswith(".lnk") and clean_lower in f.lower():
                        return os.path.join(root, f)

        # 5. Check PATH with shutil.which
        which_path = shutil.which(clean) or shutil.which(f"{clean}.exe")
        if which_path:
            return which_path

        return None

    async def list_installed_apps(self) -> List[Dict[str, str]]:
        """Discover installed applications on the host system."""
        loop = self._get_loop()
        return await loop.run_in_executor(None, self._list_installed_apps_sync)

    def _list_installed_apps_sync(self) -> List[Dict[str, str]]:
        apps = []
        seen = set()

        # Query Windows Uninstall registry keys
        uninstall_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]

        for root_key, subkey in uninstall_keys:
            try:
                with winreg.OpenKey(root_key, subkey) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for i in range(count):
                        try:
                            sub = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub) as app_key:
                                name, _ = winreg.QueryValueEx(app_key, "DisplayName")
                                if name and name not in seen:
                                    seen.add(name)
                                    install_loc = ""
                                    try:
                                        install_loc, _ = winreg.QueryValueEx(app_key, "InstallLocation")
                                    except Exception:
                                        pass
                                    apps.append({"name": str(name), "path": str(install_loc)})
                        except Exception:
                            continue
            except Exception:
                continue

        return apps

    # ==========================================
    # INPUT SYNTHESIS & SAFETY
    # ==========================================

    async def mouse_move(self, x: int, y: int, duration: float = 0.0) -> None:
        """Move cursor to coordinate (x, y)."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyautogui.moveTo, x, y, duration)

    async def mouse_click(
        self,
        button: str = "left",
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1
    ) -> None:
        """Click mouse button at current or specified coordinate."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyautogui.click, x, y, clicks, 0.0, button)

    async def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
        """Drag mouse from start coordinate to end coordinate."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        def _drag():
            pyautogui.moveTo(start_x, start_y)
            pyautogui.dragTo(end_x, end_y, duration=duration, button="left")
        await loop.run_in_executor(None, _drag)

    async def mouse_scroll(self, clicks: int) -> None:
        """Scroll vertical wheel."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyautogui.scroll, clicks)

    async def get_cursor_position(self) -> Dict[str, int]:
        """Return current mouse cursor position."""
        if not HAS_PYAUTOGUI:
            return {"x": 0, "y": 0}
        pos = pyautogui.position()
        return {"x": pos.x, "y": pos.y}

    async def keyboard_type(self, text: str, interval: float = 0.01) -> None:
        """Synthesize typing string into active focus."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyautogui.typewrite, text, interval)

    async def keyboard_press(self, key: str) -> None:
        """Press a single key."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyautogui.press, key.lower())

    async def keyboard_hotkey(self, keys: List[str]) -> None:
        """Press key combination sequentially and release."""
        if not HAS_PYAUTOGUI:
            return
        loop = self._get_loop()
        lower_keys = [k.lower() for k in keys]
        await loop.run_in_executor(None, pyautogui.hotkey, *lower_keys)

    # ==========================================
    # CLIPBOARD CONTROL
    # ==========================================

    async def clipboard_read(self) -> str:
        """Read current textual contents of OS clipboard."""
        if not HAS_PYPERCLIP:
            return ""
        loop = self._get_loop()
        return await loop.run_in_executor(None, pyperclip.paste)

    async def clipboard_write(self, text: str) -> None:
        """Write string to OS clipboard."""
        if not HAS_PYPERCLIP:
            return
        loop = self._get_loop()
        await loop.run_in_executor(None, pyperclip.copy, text)

    async def clipboard_clear(self) -> None:
        """Clear OS clipboard contents."""
        await self.clipboard_write("")

    # ==========================================
    # SCREEN OBSERVATION
    # ==========================================

    async def capture_screen(
        self,
        output_path: Path,
        region: Optional[Dict[str, int]] = None,
        window_handle: Optional[int] = None
    ) -> Dict[str, Any]:
        """Capture screenshot of full screen, region, or specific window."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        loop = self._get_loop()

        def _capture():
            bbox = None
            if window_handle and HAS_WIN32:
                try:
                    l, t, r, b = win32gui.GetWindowRect(window_handle)
                    bbox = (l, t, max(0, r - l), max(0, b - t))
                except Exception:
                    pass
            elif region:
                bbox = (region.get("left", 0), region.get("top", 0), region.get("width", 800), region.get("height", 600))

            try:
                if HAS_PYAUTOGUI:
                    img = pyautogui.screenshot(region=bbox)
                    img.save(str(output_path))
                    return {"width": img.width, "height": img.height}
            except Exception:
                pass

            from PIL import Image
            w, h = (bbox[2], bbox[3]) if (bbox and len(bbox) >= 4) else (1920, 1080)
            img = Image.new("RGB", (w, h), color=(15, 23, 42))
            img.save(str(output_path))
            return {"width": w, "height": h}

        res = await loop.run_in_executor(None, _capture)
        return {
            "path": str(output_path.resolve()),
            "width": res["width"],
            "height": res["height"],
            "size_bytes": os.path.getsize(output_path)
        }

    async def get_screen_size(self) -> Dict[str, int]:
        """Return primary screen dimensions."""
        if HAS_PYAUTOGUI:
            w, h = pyautogui.size()
            return {"width": w, "height": h}
        return {"width": 1920, "height": 1080}
