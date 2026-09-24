"""
SHIVANI App Adapters Subsystem
"""

from adapters.base import AppAdapter, AppInfo
from adapters.discovery import AppDiscovery
from adapters.windows import WindowsAppAdapter
from adapters.browser import BrowserAppAdapter
from adapters.android import AndroidAppAdapter
from adapters.registry import AdapterRegistry

__all__ = [
    "AppAdapter",
    "AppInfo",
    "AppDiscovery",
    "WindowsAppAdapter",
    "BrowserAppAdapter",
    "AndroidAppAdapter",
    "AdapterRegistry",
]
