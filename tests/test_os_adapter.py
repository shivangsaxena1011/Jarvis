"""
Unit tests for SHIVANI OS Abstraction Layer and Adapters.
"""

import pytest
from pathlib import Path
from tools.desktop.os.base import WindowInfo
from tools.desktop.os.mock import MockOSAdapter
from tools.desktop.os.windows import WindowsAdapter
from tools.desktop.os.factory import get_os_adapter, reset_os_adapter


@pytest.fixture
def mock_os():
    return MockOSAdapter()


@pytest.mark.asyncio
async def test_mock_window_management(mock_os):
    active = await mock_os.get_active_window()
    assert active is not None
    assert "Visual Studio Code" in active.title
    assert active.is_active is True

    all_wins = await mock_os.list_windows(visible_only=True)
    assert len(all_wins) == 3

    # Find by title
    chrome_wins = await mock_os.find_windows_by_title("Chrome")
    assert len(chrome_wins) == 1
    assert chrome_wins[0].handle == 1002

    # Focus Chrome
    focused = await mock_os.focus_window(1002)
    assert focused is True
    new_active = await mock_os.get_active_window()
    assert new_active.handle == 1002
    assert new_active.is_active is True

    # Minimize Chrome
    minimized = await mock_os.minimize_window(1002)
    assert minimized is True
    assert mock_os.windows[1002].is_minimized is True

    # Maximize Chrome
    maximized = await mock_os.maximize_window(1002)
    assert maximized is True
    assert mock_os.windows[1002].is_maximized is True

    # Close Chrome
    closed = await mock_os.close_window(1002)
    assert closed is True
    assert 1002 not in mock_os.windows


@pytest.mark.asyncio
async def test_mock_application_lifecycle(mock_os):
    # Resolve app path
    path = await mock_os.resolve_app_path("chrome")
    assert path is not None
    assert "chrome.exe" in path.lower()

    # Launch app
    launch_res = await mock_os.launch_app("notepad.exe")
    assert launch_res["status"] == "launched"
    assert launch_res["pid"] >= 9000

    # Verify simulated window created
    active = await mock_os.get_active_window()
    assert "notepad.exe" in active.title.lower()

    # List installed apps
    apps = await mock_os.list_installed_apps()
    assert len(apps) >= 4


@pytest.mark.asyncio
async def test_mock_input_synthesis(mock_os):
    # Mouse move
    await mock_os.mouse_move(350, 420)
    pos = await mock_os.get_cursor_position()
    assert pos == {"x": 350, "y": 420}

    # Mouse click
    await mock_os.mouse_click(button="right", x=400, y=500)
    assert len(mock_os.clicks_history) == 1
    assert mock_os.clicks_history[0]["button"] == "right"
    assert mock_os.clicks_history[0]["x"] == 400

    # Keyboard type
    await mock_os.keyboard_type("Shivani Agent")
    assert "Shivani Agent" in mock_os.typed_history

    # Keyboard press & hotkey
    await mock_os.keyboard_press("enter")
    assert "enter" in mock_os.keys_pressed

    await mock_os.keyboard_hotkey(["ctrl", "c"])
    assert ["ctrl", "c"] in mock_os.hotkeys_pressed


@pytest.mark.asyncio
async def test_mock_clipboard(mock_os):
    await mock_os.clipboard_write("Secure token 123")
    content = await mock_os.clipboard_read()
    assert content == "Secure token 123"

    await mock_os.clipboard_clear()
    cleared = await mock_os.clipboard_read()
    assert cleared == ""


@pytest.mark.asyncio
async def test_mock_screen_capture(mock_os, tmp_path):
    target = tmp_path / "mock_screenshot.png"
    res = await mock_os.capture_screen(target, region={"width": 800, "height": 600})
    assert Path(res["path"]).exists()
    assert res["width"] == 800
    assert res["height"] == 600

    screen_size = await mock_os.get_screen_size()
    assert screen_size["width"] == 1920
    assert screen_size["height"] == 1080


def test_os_adapter_factory():
    reset_os_adapter()
    mock_adapter = get_os_adapter(force_mock=True)
    assert isinstance(mock_adapter, MockOSAdapter)

    reset_os_adapter()
    default_adapter = get_os_adapter()
    assert default_adapter is not None
