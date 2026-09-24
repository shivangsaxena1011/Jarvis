"""
SHIVANI Multi-Monitor Detection and DPI Scaling Enumeration.
"""

from typing import List, Optional
import sys
import ctypes
from vision.models.types import MonitorInfo, Point, BoundingBox


def get_windows_system_dpi_scale() -> float:
    """Retrieves system DPI scale factor on Windows (e.g., 1.0, 1.25, 1.5, 2.0)."""
    if sys.platform != "win32":
        return 1.0
    try:
        # DPI awareness context: Per-Monitor High DPI Aware
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
        dpi = ctypes.windll.user32.GetDpiForSystem()
        if dpi > 0:
            return round(dpi / 96.0, 2)
    except Exception:
        pass
    return 1.0


def enumerate_monitors() -> List[MonitorInfo]:
    """Enumerates all active connected monitors with their bounds and scale factors."""
    monitors: List[MonitorInfo] = []
    scale = get_windows_system_dpi_scale()

    if sys.platform == "win32":
        try:
            import win32api
            import win32con

            enum_displays = win32api.EnumDisplayMonitors()
            for idx, (hmon, hdc, rect) in enumerate(enum_displays):
                mon_info = win32api.GetMonitorInfo(hmon)
                r = mon_info.get("Monitor", rect)
                x, y, right, bottom = r
                w = right - x
                h = bottom - y
                is_primary = bool(mon_info.get("Flags", 0) & win32con.MONITORINFOF_PRIMARY)
                monitors.append(
                    MonitorInfo(
                        id=idx,
                        name=f"Display_{idx}",
                        x=x,
                        y=y,
                        width=w,
                        height=h,
                        scale_factor=scale,
                        is_primary=is_primary,
                    )
                )
        except Exception:
            pass

    if not monitors:
        # PyAutoGUI / basic fallback
        try:
            import pyautogui
            w, h = pyautogui.size()
            monitors.append(
                MonitorInfo(
                    id=0,
                    name="Primary_Display",
                    x=0,
                    y=0,
                    width=w,
                    height=h,
                    scale_factor=scale,
                    is_primary=True,
                )
            )
        except Exception:
            monitors.append(
                MonitorInfo(
                    id=0,
                    name="Default_Display",
                    x=0,
                    y=0,
                    width=1920,
                    height=1080,
                    scale_factor=1.0,
                    is_primary=True,
                )
            )
    return monitors


def get_primary_monitor() -> MonitorInfo:
    """Returns the primary monitor or first available monitor."""
    mons = enumerate_monitors()
    for m in mons:
        if m.is_primary:
            return m
    return mons[0] if mons else MonitorInfo(id=0, name="Primary", is_primary=True)


def get_monitor_for_point(point: Point) -> MonitorInfo:
    """Finds the monitor that encloses the specified coordinate point."""
    mons = enumerate_monitors()
    for m in mons:
        if m.bounds.contains_point(point):
            return m
    return get_primary_monitor()
