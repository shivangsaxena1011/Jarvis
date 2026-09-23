"""
Unit tests for SHIVANI InputController and Registered Input Tools with Focus Safety Checks.
"""

import pytest
from tools.desktop.os.mock import MockOSAdapter
from tools.desktop.input import InputController
from tools.desktop.clipboard import ClipboardManager
from tools.desktop.input_tools import (
    MouseMoveTool,
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    TypeTool,
    PressKeyTool,
    HotkeyTool,
    GetCursorPosTool,
)
from tools.desktop.clipboard_tools import (
    ClipboardReadTool,
    ClipboardWriteTool,
    ClipboardClearTool,
)
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine


@pytest.fixture
def input_setup():
    adapter = MockOSAdapter()
    ctrl = InputController(adapter)
    clip = ClipboardManager(adapter)
    return adapter, ctrl, clip


@pytest.mark.asyncio
async def test_input_safety_focus_validation(input_setup):
    adapter, ctrl, _ = input_setup

    # 1. Target window matches current active window ("Visual Studio Code") -> succeeds directly
    res = await ctrl.type_text("print('hello')", target_window="Visual Studio Code")
    assert res["success"] is True
    assert "print('hello')" in adapter.typed_history

    # 2. Target window is different ("Google Chrome") -> auto-refocuses target window and succeeds
    res_chrome = await ctrl.type_text("google.com", target_window="Google Chrome")
    assert res_chrome["success"] is True
    assert adapter.windows[1002].is_active is True
    assert "google.com" in adapter.typed_history

    # 3. Target window does not exist -> Input Safety Violation error raised
    with pytest.raises(RuntimeError, match="Input Safety Violation"):
        await ctrl.type_text("malicious text", target_window="NonExistentApp123")


@pytest.mark.asyncio
async def test_mouse_actions(input_setup):
    adapter, ctrl, _ = input_setup

    # Move
    move_res = await ctrl.mouse_move(200, 300)
    assert move_res["x"] == 200
    assert move_res["y"] == 300

    # Click with focus check
    click_res = await ctrl.click(button="left", x=250, y=350, target_window="Visual Studio Code")
    assert click_res["success"] is True
    assert click_res["button"] == "left"
    assert click_res["x"] == 250
    assert click_res["y"] == 350

    # Double click
    db_res = await ctrl.double_click(x=100, y=100)
    assert db_res["clicks"] == 2

    # Right click
    rc_res = await ctrl.right_click(x=150, y=150)
    assert rc_res["button"] == "right"

    # Drag
    drag_res = await ctrl.drag(0, 0, 50, 50)
    assert drag_res["success"] is True

    # Position
    pos = await ctrl.get_cursor_position()
    assert pos["x"] == 50
    assert pos["y"] == 50


@pytest.mark.asyncio
async def test_registered_input_tools(input_setup):
    adapter, ctrl, clip = input_setup
    perm = PermissionEngine(policy="test")
    reg = ToolRegistry(permission_engine=perm)

    type_tool = TypeTool(input_controller=ctrl)
    press_tool = PressKeyTool(input_controller=ctrl)
    hotkey_tool = HotkeyTool(input_controller=ctrl)
    click_tool = ClickTool(input_controller=ctrl)
    clip_read = ClipboardReadTool(clipboard_manager=clip)
    clip_write = ClipboardWriteTool(clipboard_manager=clip)
    clip_clear = ClipboardClearTool(clipboard_manager=clip)

    reg.register(type_tool)
    reg.register(press_tool)
    reg.register(hotkey_tool)
    reg.register(click_tool)
    reg.register(clip_read)
    reg.register(clip_write)
    reg.register(clip_clear)

    # 1. Type
    res_type = await reg.execute_tool("computer.type", {"text": "hello shivani", "target_window": "Visual Studio Code"})
    assert res_type.success is True
    assert res_type.verification["verified"] is True

    # 2. Press
    res_press = await reg.execute_tool("computer.press_key", {"key": "enter"})
    assert res_press.success is True

    # 3. Hotkey
    res_hotkey = await reg.execute_tool("computer.hotkey", {"keys": ["ctrl", "s"]})
    assert res_hotkey.success is True

    # 4. Clipboard write, read, clear
    res_cw = await reg.execute_tool("clipboard.write", {"text": "secret-clipboard-text"})
    assert res_cw.success is True

    res_cr = await reg.execute_tool("clipboard.read", {})
    assert res_cr.success is True
    assert res_cr.data["content"] == "secret-clipboard-text"

    res_cc = await reg.execute_tool("clipboard.clear", {})
    assert res_cc.success is True
    res_cr2 = await reg.execute_tool("clipboard.read", {})
    assert res_cr2.data["content"] == ""
