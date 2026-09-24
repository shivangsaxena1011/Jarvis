"""Tests for registration and execution of all 22 Android Phone tools."""

import pytest
from core.orchestrator.orchestrator import Orchestrator


@pytest.mark.asyncio
async def test_all_22_android_tools_registered():
    orchestrator = Orchestrator()
    raw_tools = orchestrator.tools.list_tools()
    tool_names = [t["name"] if isinstance(t, dict) else t for t in raw_tools]

    expected_tools = [
        "android.get_device_status",
        "android.pair_device",
        "android.disconnect_device",
        "android.launch_app",
        "android.close_app",
        "android.open_settings",
        "android.press_home",
        "android.press_back",
        "android.screenshot",
        "android.get_visible_ui",
        "android.tap",
        "android.long_press",
        "android.swipe",
        "android.type",
        "android.list_photos",
        "android.select_photo",
        "android.transfer_file",
        "android.get_notifications",
        "android.read_clipboard",
        "android.write_clipboard",
        "android.prepare_social_action",
        "android.execute_social_action",
    ]

    for tool in expected_tools:
        assert tool in tool_names, f"Expected tool '{tool}' not found in registry."

    # Verify execution of representative tools
    res1 = await orchestrator.tools.execute_tool(name="android.get_device_status", arguments={})
    assert res1.success is True
    assert res1.data["battery_level"] == 88

    res2 = await orchestrator.tools.execute_tool(name="android.launch_app", arguments={"app_name": "Instagram"})
    assert res2.success is True
    assert res2.data["package"] == "com.instagram.android"

    res3 = await orchestrator.tools.execute_tool(name="android.list_photos", arguments={"query": "hackathon"})
    assert res3.success is True
    assert res3.data["count"] >= 1
