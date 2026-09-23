"""
Unit tests for SHIVANI WindowManager and registered Window Tools.
"""

import pytest
from tools.desktop.os.mock import MockOSAdapter
from tools.desktop.window import WindowManager
from tools.desktop.window_tools import (
    WindowListTool,
    WindowFocusTool,
    WindowMinimizeTool,
    WindowMaximizeTool,
    WindowRestoreTool,
    WindowCloseTool,
)
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine


@pytest.fixture
def window_setup():
    adapter = MockOSAdapter()
    manager = WindowManager(adapter)
    return adapter, manager


@pytest.mark.asyncio
async def test_window_manager_operations(window_setup):
    adapter, manager = window_setup

    # 1. List
    wins = await manager.list_windows()
    assert len(wins) == 3

    # 2. Find
    chrome = await manager.find_window("Chrome")
    assert chrome is not None
    assert chrome.handle == 1002

    # 3. Focus
    focus_res = await manager.focus_window("Chrome")
    assert focus_res["verified"] is True
    assert focus_res["focused"] is True

    # 4. Minimize
    min_res = await manager.minimize_window("Chrome")
    assert min_res["verified"] is True

    # 5. Maximize
    max_res = await manager.maximize_window("Chrome")
    assert max_res["verified"] is True

    # 6. Restore
    rest_res = await manager.restore_window("Chrome")
    assert rest_res["verified"] is True

    # 7. Close
    close_res = await manager.close_window("Chrome")
    assert close_res["verified"] is True
    assert 1002 not in adapter.windows


@pytest.mark.asyncio
async def test_registered_window_tools(window_setup):
    adapter, manager = window_setup
    perm = PermissionEngine(policy="test")
    reg = ToolRegistry(permission_engine=perm)

    list_tool = WindowListTool(window_manager=manager)
    focus_tool = WindowFocusTool(window_manager=manager)
    min_tool = WindowMinimizeTool(window_manager=manager)
    max_tool = WindowMaximizeTool(window_manager=manager)
    close_tool = WindowCloseTool(window_manager=manager)

    reg.register(list_tool)
    reg.register(focus_tool)
    reg.register(min_tool)
    reg.register(max_tool)
    reg.register(close_tool)

    # Execute window.list
    res_list = await reg.execute_tool("window.list", {"visible_only": True})
    assert res_list.success is True
    assert len(res_list.data) == 3

    # Execute window.focus
    res_focus = await reg.execute_tool("window.focus", {"title_or_handle": "Chrome"})
    assert res_focus.success is True
    assert res_focus.verification["verified"] is True

    # Execute window.minimize
    res_min = await reg.execute_tool("window.minimize", {"title_or_handle": "Chrome"})
    assert res_min.success is True
    assert res_min.verification["verified"] is True

    # Execute window.close
    res_close = await reg.execute_tool("window.close", {"title_or_handle": "Chrome"})
    assert res_close.success is True
    assert res_close.verification["verified"] is True
