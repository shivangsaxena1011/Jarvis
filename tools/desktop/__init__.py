from tools.desktop.application import ApplicationManager
from tools.desktop.window import WindowManager
from tools.desktop.input import InputController
from tools.desktop.screen import ScreenCapture
from tools.desktop.clipboard import ClipboardManager

from tools.desktop.app_tools import (
    OpenAppTool,
    CloseAppTool,
    FocusAppTool,
    ListAppsTool,
    ActiveWindowTool,
)
from tools.desktop.window_tools import (
    WindowListTool,
    WindowFocusTool,
    WindowMinimizeTool,
    WindowMaximizeTool,
    WindowRestoreTool,
    WindowCloseTool,
)
from tools.desktop.input_tools import (
    MouseMoveTool,
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    MouseDragTool,
    MouseScrollTool,
    GetCursorPosTool,
    TypeTool,
    PressKeyTool,
    HotkeyTool,
)
from tools.desktop.clipboard_tools import (
    ClipboardReadTool,
    ClipboardWriteTool,
    ClipboardClearTool,
)
from tools.desktop.screen_tools import ScreenshotTool
from tools.desktop.file_explorer_tools import OpenFolderTool, FindFilesTool

__all__ = [
    # Managers
    "ApplicationManager",
    "WindowManager",
    "InputController",
    "ScreenCapture",
    "ClipboardManager",
    # Tools
    "OpenAppTool",
    "CloseAppTool",
    "FocusAppTool",
    "ListAppsTool",
    "ActiveWindowTool",
    "WindowListTool",
    "WindowFocusTool",
    "WindowMinimizeTool",
    "WindowMaximizeTool",
    "WindowRestoreTool",
    "WindowCloseTool",
    "MouseMoveTool",
    "ClickTool",
    "DoubleClickTool",
    "RightClickTool",
    "MouseDragTool",
    "MouseScrollTool",
    "GetCursorPosTool",
    "TypeTool",
    "PressKeyTool",
    "HotkeyTool",
    "ClipboardReadTool",
    "ClipboardWriteTool",
    "ClipboardClearTool",
    "ScreenshotTool",
    "OpenFolderTool",
    "FindFilesTool",
]
