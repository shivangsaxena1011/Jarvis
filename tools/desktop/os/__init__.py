from tools.desktop.os.base import OperatingSystemAdapter, WindowInfo
from tools.desktop.os.windows import WindowsAdapter
from tools.desktop.os.mock import MockOSAdapter
from tools.desktop.os.factory import get_os_adapter, reset_os_adapter

__all__ = [
    "OperatingSystemAdapter",
    "WindowInfo",
    "WindowsAdapter",
    "MockOSAdapter",
    "get_os_adapter",
    "reset_os_adapter",
]
