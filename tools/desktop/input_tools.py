"""
SHIVANI Input Tools
Provides registered tools for mouse movement, clicking, dragging,
scrolling, keyboard typing, key presses, and hotkeys.
All tools enforce target window focus validation safety checks.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.input import InputController


# ==========================================
# MOUSE SCHEMAS & TOOLS
# ==========================================

class MouseMoveArgs(BaseModel):
    x: int = Field(description="Target X pixel coordinate on screen")
    y: int = Field(description="Target Y pixel coordinate on screen")


class MouseMoveTool(BaseTool):
    name = "computer.mouse_move"
    description = "Move mouse cursor to specified (x, y) screen coordinates."
    permission_level = RiskLevel.SAFE
    args_schema = MouseMoveArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, x: int, y: int) -> Dict[str, Any]:
        return await self.input_controller.mouse_move(x, y)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class MouseClickArgs(BaseModel):
    x: Optional[int] = Field(default=None, description="Optional X pixel coordinate to click at")
    y: Optional[int] = Field(default=None, description="Optional Y pixel coordinate to click at")
    button: str = Field(default="left", description="Mouse button ('left', 'right', 'middle')")
    target_window: Optional[str] = Field(default=None, description="Expected window title or app to focus before clicking")


class ClickTool(BaseTool):
    name = "computer.click"
    description = "Click mouse button at current or specified coordinate with target focus safety."
    permission_level = RiskLevel.SAFE
    args_schema = MouseClickArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.input_controller.click(button=button, x=x, y=y, clicks=1, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class DoubleClickTool(BaseTool):
    name = "computer.double_click"
    description = "Perform mouse double-click at current or specified coordinate."
    permission_level = RiskLevel.SAFE
    args_schema = MouseClickArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.input_controller.double_click(x=x, y=y, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class RightClickTool(BaseTool):
    name = "computer.right_click"
    description = "Perform mouse right-click (context menu) at current or specified coordinate."
    permission_level = RiskLevel.SAFE
    args_schema = MouseClickArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "right",
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        return await self.input_controller.right_click(x=x, y=y, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class MouseDragArgs(BaseModel):
    start_x: int = Field(description="Starting X coordinate")
    start_y: int = Field(description="Starting Y coordinate")
    end_x: int = Field(description="Ending X coordinate")
    end_y: int = Field(description="Ending Y coordinate")


class MouseDragTool(BaseTool):
    name = "computer.drag"
    description = "Drag mouse from start coordinate to end coordinate."
    permission_level = RiskLevel.SAFE
    args_schema = MouseDragArgs
    timeout = 4.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, start_x: int, start_y: int, end_x: int, end_y: int) -> Dict[str, Any]:
        return await self.input_controller.drag(start_x, start_y, end_x, end_y)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class MouseScrollArgs(BaseModel):
    clicks: int = Field(description="Number of wheel clicks (positive for up, negative for down)")


class MouseScrollTool(BaseTool):
    name = "computer.scroll"
    description = "Scroll mouse wheel up or down."
    permission_level = RiskLevel.SAFE
    args_schema = MouseScrollArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, clicks: int) -> Dict[str, Any]:
        return await self.input_controller.scroll(clicks)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class GetCursorPosTool(BaseTool):
    name = "computer.get_cursor_position"
    description = "Get current mouse cursor screen coordinates."
    permission_level = RiskLevel.SAFE
    timeout = 2.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self) -> Dict[str, int]:
        return await self.input_controller.get_cursor_position()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": "x" in result_data and "y" in result_data}


# ==========================================
# KEYBOARD SCHEMAS & TOOLS
# ==========================================

class TypeArgs(BaseModel):
    text: str = Field(description="Text to type into active focus")
    target_window: Optional[str] = Field(default=None, description="Expected window title/app to verify before typing")


class TypeTool(BaseTool):
    name = "computer.type"
    description = "Type text characters into focused window with target validation safety."
    permission_level = RiskLevel.SENSITIVE
    args_schema = TypeArgs
    timeout = 10.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, text: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        return await self.input_controller.type_text(text, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False), "typed": result_data.get("characters_typed", 0)}


class PressKeyArgs(BaseModel):
    key: str = Field(description="Key to press (e.g. 'enter', 'tab', 'esc', 'backspace', 'down')")
    target_window: Optional[str] = Field(default=None, description="Expected window title/app to verify before press")


class PressKeyTool(BaseTool):
    name = "computer.press_key"
    description = "Press a single keyboard key (e.g. Enter, Esc, Tab, Space)."
    permission_level = RiskLevel.SAFE
    args_schema = PressKeyArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, key: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        return await self.input_controller.press_key(key, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class HotkeyArgs(BaseModel):
    keys: List[str] = Field(description="Key sequence to press simultaneously (e.g. ['ctrl', 'c'], ['ctrl', 'shift', 'p'])")
    target_window: Optional[str] = Field(default=None, description="Expected window title/app to verify before hotkey")


class HotkeyTool(BaseTool):
    name = "computer.hotkey"
    description = "Send keyboard shortcut combination (e.g. Ctrl+C, Ctrl+V, Ctrl+Shift+P)."
    permission_level = RiskLevel.SAFE
    args_schema = HotkeyArgs
    timeout = 3.0

    def __init__(self, input_controller: Optional[InputController] = None):
        super().__init__()
        self.input_controller = input_controller or InputController()

    async def run(self, keys: List[str], target_window: Optional[str] = None) -> Dict[str, Any]:
        return await self.input_controller.hotkey(keys, target_window=target_window)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}
