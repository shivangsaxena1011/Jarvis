"""
Tests for App Adapters: discovery, WindowsAppAdapter, BrowserAppAdapter, AndroidAppAdapter,
and AdapterRegistry.
"""

import pytest
from adapters.android import AndroidAppAdapter
from adapters.base import AppInfo
from adapters.browser import BrowserAppAdapter
from adapters.discovery import AppDiscovery
from adapters.registry import AdapterRegistry
from adapters.windows import WindowsAppAdapter


def test_app_discovery_caching():
    discovery = AppDiscovery()
    apps = discovery.discover_installed_apps()
    assert isinstance(apps, list)

    # find_app works
    notepad_info = discovery.find_app("notepad")
    if notepad_info:
        assert notepad_info.name.lower() == "notepad"


@pytest.mark.asyncio
async def test_browser_adapter():
    adapter = BrowserAppAdapter()
    assert await adapter.is_available() is True
    assert adapter.app_type == "browser"

    launched = await adapter.launch(url="https://example.com")
    assert launched is True

    state = await adapter.get_state()
    assert state["type"] == "browser"


@pytest.mark.asyncio
async def test_android_adapter():
    adapter = AndroidAppAdapter(app_name="instagram", package_name="com.instagram.android")
    assert adapter.app_type == "mobile"
    assert await adapter.is_available() is True

    launched = await adapter.launch()
    assert launched is True


def test_adapter_registry():
    registry = AdapterRegistry()
    b_adapter = BrowserAppAdapter()
    m_adapter = AndroidAppAdapter("whatsapp", "com.whatsapp")

    registry.register_adapter(b_adapter)
    registry.register_adapter(m_adapter)

    assert registry.get_adapter("browser") is not None
    assert registry.get_adapter("whatsapp") is not None

    mobiles = registry.list_adapters(app_type="mobile")
    assert len(mobiles) == 1
    assert mobiles[0].name == "whatsapp"
