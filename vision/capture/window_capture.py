"""
SHIVANI Window Capture and Target Application Extraction.
"""

from typing import Optional, Dict, Any, Tuple
import os
import time
import tempfile
import sys
from PIL import Image

from vision.models.types import BoundingBox, CoordinateSpace
from vision.capture.screen_capture import ScreenCaptureEngine


class WindowCaptureEngine:
    """Captures specific application windows without background desktop clutter."""

    def __init__(self, screen_capture: Optional[ScreenCaptureEngine] = None):
        self.screen_capture = screen_capture or ScreenCaptureEngine()

    def get_active_window_info(self) -> Dict[str, Any]:
        """Returns metadata about the currently foreground active window."""
        info: Dict[str, Any] = {
            "title": "Desktop",
            "hwnd": 0,
            "rect": {"x": 0, "y": 0, "width": 1920, "height": 1080},
        }

        if sys.platform == "win32":
            try:
                import win32gui
                import win32process
                import psutil

                hwnd = win32gui.GetForegroundWindow()
                if hwnd:
                    title = win32gui.GetWindowText(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    x, y, r, b = rect
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    pname = psutil.Process(pid).name() if pid else "unknown"

                    info = {
                        "title": title or "Untitled Window",
                        "hwnd": hwnd,
                        "pid": pid,
                        "process": pname,
                        "rect": {
                            "x": x,
                            "y": y,
                            "width": max(1, r - x),
                            "height": max(1, b - y),
                        },
                    }
            except Exception:
                pass

        return info

    def capture_active_window(
        self,
        save_path: Optional[str] = None
    ) -> Tuple[str, Dict[str, Any], Image.Image]:
        """Captures the bounding box of the active foreground window."""
        win_info = self.get_active_window_info()
        rect = win_info["rect"]

        box = BoundingBox(
            x=float(rect["x"]),
            y=float(rect["y"]),
            width=float(rect["width"]),
            height=float(rect["height"]),
            coordinate_space=CoordinateSpace.LOGICAL,
        )

        saved_path, img = self.screen_capture.capture_region(box, save_path=save_path)
        return (saved_path, win_info, img)
