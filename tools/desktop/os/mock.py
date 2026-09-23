"""
SHIVANI Mock Operating System Adapter
Deterministic in-memory mock for automated unit testing and headless CI.
Simulates windows, processes, clipboard, input events, and display captures.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from PIL import Image

from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo


class MockOSAdapter(OperatingSystemAdapter):
    """In-memory mock adapter for cross-platform deterministic test execution."""

    def __init__(self):
        self.windows: Dict[int, WindowInfo] = {
            1001: WindowInfo(
                handle=1001,
                title="Visual Studio Code - Shivani",
                pid=5010,
                app_name="Code.exe",
                rect={"left": 100, "top": 100, "width": 1200, "height": 800},
                is_active=True,
                is_minimized=False,
                is_maximized=False,
                is_visible=True,
            ),
            1002: WindowInfo(
                handle=1002,
                title="Google Chrome",
                pid=5020,
                app_name="chrome.exe",
                rect={"left": 200, "top": 200, "width": 1000, "height": 700},
                is_active=False,
                is_minimized=False,
                is_maximized=False,
                is_visible=True,
            ),
            1003: WindowInfo(
                handle=1003,
                title="Untitled - Notepad",
                pid=5030,
                app_name="notepad.exe",
                rect={"left": 300, "top": 300, "width": 600, "height": 400},
                is_active=False,
                is_minimized=False,
                is_maximized=False,
                is_visible=True,
            ),
        }
        self.cursor_pos = {"x": 500, "y": 500}
        self.clipboard_data = ""
        self.typed_history: List[str] = []
        self.keys_pressed: List[str] = []
        self.hotkeys_pressed: List[List[str]] = []
        self.clicks_history: List[Dict[str, Any]] = []
        self.launched_processes: List[Dict[str, Any]] = []

    async def get_active_window(self) -> Optional[WindowInfo]:
        for win in self.windows.values():
            if win.is_active:
                return win
        return None

    async def list_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        if visible_only:
            return [w for w in self.windows.values() if w.is_visible]
        return list(self.windows.values())

    async def find_windows_by_title(self, query: str, visible_only: bool = True) -> List[WindowInfo]:
        q = query.lower()
        return [
            w for w in self.windows.values()
            if (not visible_only or w.is_visible) and (q in w.title.lower() or (w.app_name and q in w.app_name.lower()))
        ]

    def _find_window(self, identifier: Any) -> Optional[WindowInfo]:
        if isinstance(identifier, int):
            return self.windows.get(identifier)
        if isinstance(identifier, WindowInfo):
            return self.windows.get(identifier.handle)
        if isinstance(identifier, str):
            q = identifier.lower()
            for win in self.windows.values():
                if q in win.title.lower() or (win.app_name and q in win.app_name.lower()):
                    return win
        return None

    async def focus_window(self, identifier: Any) -> bool:
        target = self._find_window(identifier)
        if not target:
            return False
        for win in self.windows.values():
            win.is_active = (win.handle == target.handle)
        target.is_minimized = False
        return True

    async def minimize_window(self, identifier: Any) -> bool:
        target = self._find_window(identifier)
        if not target:
            return False
        target.is_minimized = True
        target.is_active = False
        return True

    async def maximize_window(self, identifier: Any) -> bool:
        target = self._find_window(identifier)
        if not target:
            return False
        target.is_maximized = True
        target.is_minimized = False
        target.is_active = True
        return True

    async def restore_window(self, identifier: Any) -> bool:
        target = self._find_window(identifier)
        if not target:
            return False
        target.is_minimized = False
        target.is_maximized = False
        return True

    async def close_window(self, identifier: Any) -> bool:
        target = self._find_window(identifier)
        if not target:
            return False
        self.windows.pop(target.handle, None)
        return True

    async def launch_app(self, executable: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        pid = 9000 + len(self.launched_processes)
        clean_name = Path(executable).name
        # Create simulated window for newly launched app
        hwnd = 2000 + len(self.windows)
        new_win = WindowInfo(
            handle=hwnd,
            title=f"{clean_name} Window",
            pid=pid,
            app_name=clean_name,
            rect={"left": 100, "top": 100, "width": 800, "height": 600},
            is_active=True,
            is_minimized=False,
            is_maximized=False,
            is_visible=True,
        )
        # Set previous windows active=False
        for w in self.windows.values():
            w.is_active = False
        self.windows[hwnd] = new_win

        record = {"pid": pid, "executable": executable, "args": args or [], "status": "launched"}
        self.launched_processes.append(record)
        return record

    async def resolve_app_path(self, app_name: str) -> Optional[str]:
        clean = app_name.lower().replace(".exe", "")
        known = {
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "google chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            "vs code": r"C:\Users\test\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "code": r"C:\Users\test\AppData\Local\Programs\Microsoft VS Code\Code.exe",
            "notepad": r"C:\Windows\System32\notepad.exe",
            "calc": r"C:\Windows\System32\calc.exe",
            "calculator": r"C:\Windows\System32\calc.exe",
            "explorer": r"C:\Windows\explorer.exe",
        }
        return known.get(clean, f"C:\\Program Files\\{app_name}\\{app_name}.exe")

    async def list_installed_apps(self) -> List[Dict[str, str]]:
        return [
            {"name": "Google Chrome", "path": r"C:\Program Files\Google\Chrome\Application\chrome.exe"},
            {"name": "Visual Studio Code", "path": r"C:\Program Files\Microsoft VS Code\Code.exe"},
            {"name": "Notepad", "path": r"C:\Windows\System32\notepad.exe"},
            {"name": "Calculator", "path": r"C:\Windows\System32\calc.exe"},
        ]

    async def mouse_move(self, x: int, y: int, duration: float = 0.0) -> None:
        self.cursor_pos = {"x": x, "y": y}

    async def mouse_click(
        self,
        button: str = "left",
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1
    ) -> None:
        if x is not None and y is not None:
            self.cursor_pos = {"x": x, "y": y}
        self.clicks_history.append({"button": button, "x": self.cursor_pos["x"], "y": self.cursor_pos["y"], "clicks": clicks})

    async def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
        self.cursor_pos = {"x": end_x, "y": end_y}

    async def mouse_scroll(self, clicks: int) -> None:
        pass

    async def get_cursor_position(self) -> Dict[str, int]:
        return dict(self.cursor_pos)

    async def keyboard_type(self, text: str, interval: float = 0.01) -> None:
        self.typed_history.append(text)

    async def keyboard_press(self, key: str) -> None:
        self.keys_pressed.append(key)

    async def keyboard_hotkey(self, keys: List[str]) -> None:
        self.hotkeys_pressed.append(keys)

    async def clipboard_read(self) -> str:
        return self.clipboard_data

    async def clipboard_write(self, text: str) -> None:
        self.clipboard_data = text

    async def clipboard_clear(self) -> None:
        self.clipboard_data = ""

    async def capture_screen(
        self,
        output_path: Path,
        region: Optional[Dict[str, int]] = None,
        window_handle: Optional[int] = None
    ) -> Dict[str, Any]:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        w, h = (region["width"], region["height"]) if region else (1920, 1080)
        img = Image.new("RGB", (w, h), color=(20, 30, 48))
        img.save(str(output_path))
        return {
            "path": str(output_path.resolve()),
            "width": w,
            "height": h,
            "size_bytes": os.path.getsize(output_path)
        }

    async def get_screen_size(self) -> Dict[str, int]:
        return {"width": 1920, "height": 1080}
