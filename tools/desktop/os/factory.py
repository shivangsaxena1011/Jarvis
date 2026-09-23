"""
SHIVANI OS Adapter Factory
Selects the appropriate OS adapter based on current host operating system.
"""

import sys
from typing import Optional
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.windows import WindowsAdapter
from tools.desktop.os.mock import MockOSAdapter

_CURRENT_ADAPTER: Optional[OperatingSystemAdapter] = None


def get_os_adapter(force_mock: bool = False) -> OperatingSystemAdapter:
    """Returns singleton OperatingSystemAdapter instance."""
    global _CURRENT_ADAPTER
    if force_mock:
        return MockOSAdapter()

    if _CURRENT_ADAPTER is None:
        if sys.platform == "win32":
            _CURRENT_ADAPTER = WindowsAdapter()
        else:
            _CURRENT_ADAPTER = MockOSAdapter()

    return _CURRENT_ADAPTER


def reset_os_adapter() -> None:
    global _CURRENT_ADAPTER
    _CURRENT_ADAPTER = None
