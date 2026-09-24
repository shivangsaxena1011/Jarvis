"""
SHIVANI App Adapter Registry
Maintains registry of application adapters across Desktop, Browser, and Mobile,
supporting on-demand desktop app adapter creation via AppDiscovery.
"""

import logging
from typing import Dict, List, Optional

from adapters.base import AppAdapter
from adapters.discovery import AppDiscovery
from adapters.windows import WindowsAppAdapter

logger = logging.getLogger("shivani.adapters.registry")


class AdapterRegistry:
    """Registry managing unified app adapters across all execution surfaces."""

    def __init__(self, discovery: Optional[AppDiscovery] = None):
        self._adapters: Dict[str, AppAdapter] = {}
        self.discovery = discovery or AppDiscovery()

    def register_adapter(self, adapter: AppAdapter) -> None:
        self._adapters[adapter.name.lower()] = adapter
        logger.info(f"Registered {adapter.app_type} adapter: '{adapter.name}'")

    def unregister_adapter(self, name: str) -> bool:
        n = name.lower()
        if n in self._adapters:
            del self._adapters[n]
            return True
        return False

    def get_adapter(self, name: str) -> Optional[AppAdapter]:
        """Gets registered adapter or discovers and mounts desktop app adapter on demand."""
        n = name.lower()
        if n in self._adapters:
            return self._adapters[n]

        # On-demand discovery
        app_info = self.discovery.find_app(name)
        if app_info:
            adapter = WindowsAppAdapter(app_info.name, app_info.executable_path)
            self.register_adapter(adapter)
            return adapter

        return None

    def list_adapters(self, app_type: Optional[str] = None) -> List[AppAdapter]:
        adapters = list(self._adapters.values())
        if app_type:
            return [a for a in adapters if a.app_type == app_type]
        return adapters
