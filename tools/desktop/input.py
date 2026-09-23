"""
SHIVANI Desktop Input Controller
Coordinates mouse and keyboard actions with strict Focus and Target Safety checks.
Prevents unintended typing or clicking into wrong foreground applications.
"""

import asyncio
from typing import Any, Dict, List, Optional
from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo
from tools.desktop.os.factory import get_os_adapter
from core.config import get_settings


class InputController:
    """Safely synthesizes input events ensuring proper window focus."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()
        self.settings = get_settings()

    async def ensure_focus(self, target_window_query: Optional[str] = None) -> bool:
        """
        Validates whether target application/window is currently active.
        If not active, automatically refocuses target window before action.
        """
        if not target_window_query:
            return True

        active = await self.adapter.get_active_window()
        q = target_window_query.lower().strip()

        # Check if already active
        if active:
            if q in active.title.lower() or (active.app_name and q in active.app_name.lower()):
                return True

        # Need to refocus target window
        windows = await self.adapter.find_windows_by_title(target_window_query, visible_only=True)
        if not windows:
            return False

        focused = await self.adapter.focus_window(windows[0])
        await asyncio.sleep(0.15)
        return focused

    # ==========================================
    # MOUSE ACTIONS
    # ==========================================

    async def mouse_move(self, x: int, y: int) -> Dict[str, Any]:
        """Moves cursor to absolute coordinate (x, y)."""
        await self.adapter.mouse_move(x, y)
        current = await self.adapter.get_cursor_position()
        return {"x": current["x"], "y": current["y"], "success": True}

    async def click(
        self,
        button: str = "left",
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1,
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely clicks at coordinate after verifying target window focus.
        """
        if target_window:
            focus_ok = await self.ensure_focus(target_window)
            if not focus_ok:
                raise RuntimeError(
                    f"Input Safety Violation: Target window '{target_window}' could not be focused before click."
                )

        await self.adapter.mouse_click(button=button, x=x, y=y, clicks=clicks)
        pos = await self.adapter.get_cursor_position()
        return {
            "button": button,
            "x": pos["x"],
            "y": pos["y"],
            "clicks": clicks,
            "target_window": target_window,
            "success": True
        }

    async def double_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """Safely performs double click."""
        return await self.click(button="left", x=x, y=y, clicks=2, target_window=target_window)

    async def right_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """Safely performs right click."""
        return await self.click(button="right", x=x, y=y, clicks=1, target_window=target_window)

    async def drag(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        """Drags mouse between coordinates."""
        await self.adapter.mouse_drag(start_x, start_y, end_x, end_y)
        return {"start": (start_x, start_y), "end": (end_x, end_y), "success": True}

    async def scroll(self, clicks: int) -> Dict[str, Any]:
        """Scrolls vertical mouse wheel."""
        await self.adapter.mouse_scroll(clicks)
        return {"scroll_clicks": clicks, "success": True}

    async def get_cursor_position(self) -> Dict[str, int]:
        """Returns current cursor position."""
        return await self.adapter.get_cursor_position()

    # ==========================================
    # KEYBOARD ACTIONS
    # ==========================================

    async def type_text(
        self,
        text: str,
        target_window: Optional[str] = None,
        interval: float = 0.01
    ) -> Dict[str, Any]:
        """
        Safely types text into target window after verifying active focus.
        """
        if target_window:
            focus_ok = await self.ensure_focus(target_window)
            if not focus_ok:
                raise RuntimeError(
                    f"Input Safety Violation: Target window '{target_window}' could not be focused before typing."
                )

        await self.adapter.keyboard_type(text, interval=interval)
        return {
            "characters_typed": len(text),
            "target_window": target_window,
            "success": True
        }

    async def press_key(self, key: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """Safely presses a key into active or specified target window."""
        if target_window:
            focus_ok = await self.ensure_focus(target_window)
            if not focus_ok:
                raise RuntimeError(
                    f"Input Safety Violation: Target window '{target_window}' could not be focused before key press."
                )

        await self.adapter.keyboard_press(key)
        return {"key": key, "target_window": target_window, "success": True}

    async def hotkey(self, keys: List[str], target_window: Optional[str] = None) -> Dict[str, Any]:
        """Safely sends hotkey combination."""
        if target_window:
            focus_ok = await self.ensure_focus(target_window)
            if not focus_ok:
                raise RuntimeError(
                    f"Input Safety Violation: Target window '{target_window}' could not be focused before hotkey."
                )

        await self.adapter.keyboard_hotkey(keys)
        return {"keys": keys, "target_window": target_window, "success": True}
