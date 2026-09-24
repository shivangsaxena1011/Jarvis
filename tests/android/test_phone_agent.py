"""Tests for SHIVANI PhoneAgent and Mobile Workflows."""

import pytest
from core.bridge.device_bridge import DeviceBridge
from core.bridge.mock_device import MockAndroidDevice
from core.bridge.models import DeviceIdentity
from agents.phone.agent import PhoneAgent
from agents.phone.app_resolver import AppResolver


@pytest.fixture
def phone_agent_fixture():
    bridge = DeviceBridge()
    mock_dev = MockAndroidDevice(device_id="shivani-android-001")
    bridge.register_transport_handler(mock_dev.handle_command)

    dev = DeviceIdentity(
        device_id="shivani-android-001",
        device_name="Shivani Phone",
        pairing_state="paired",
        connection_status="connected"
    )
    bridge.register_paired_device(dev)
    agent = PhoneAgent(bridge=bridge)
    return agent, mock_dev


def test_app_resolver_natural_language():
    resolver = AppResolver()

    # English & Hinglish queries
    assert resolver.resolve_package("Instagram") == "com.instagram.android"
    assert resolver.resolve_package("Instagram kholo") == "com.instagram.android"
    assert resolver.resolve_package("phone mein Instagram kholo") == "com.instagram.android"
    assert resolver.resolve_package("phone pe Instagram open karo") == "com.instagram.android"
    assert resolver.resolve_package("phone ki settings kholo") == "com.android.settings"
    assert resolver.resolve_package("meri photos kholo") == "com.google.android.apps.photos"
    assert resolver.resolve_package("phone pe Chrome kholo") == "com.android.chrome"
    assert resolver.resolve_package("phone pe YouTube kholo") == "com.google.android.youtube"
    assert resolver.resolve_package("YouTube chalao") == "com.google.android.youtube"
    assert resolver.resolve_package("phone mein LinkedIn kholo") == "com.linkedin.android"


def test_app_launch_and_verification(phone_agent_fixture):
    agent, mock_dev = phone_agent_fixture

    # 1. Launch Instagram
    res = agent.launch_app("phone mein Instagram kholo")
    assert res["success"] is True
    assert res["package"] == "com.instagram.android"
    assert res["status"] == "launched_and_verified"
    assert agent.context.current_package == "com.instagram.android"

    # 2. Check visible UI elements
    obs = agent.get_visible_ui()
    assert obs is not None
    assert obs.package_name == "com.instagram.android"
    assert len(obs.elements) > 0

    # 3. Screenshot capture
    shot = agent.screenshot()
    assert shot["success"] is True
    assert shot["has_image"] is True


def test_ui_interaction_and_navigation(phone_agent_fixture):
    agent, mock_dev = phone_agent_fixture

    # Open Settings
    nav_res = agent.navigate("settings")
    assert nav_res["success"] is True
    assert agent.context.current_package == "com.android.settings"

    # Tap on Accessibility item
    tap_res = agent.tap_element("Accessibility")
    assert tap_res["success"] is True
    assert "Accessibility" in tap_res["target_text"]

    # Press Home
    home_res = agent.navigate("home")
    assert home_res["success"] is True
    assert agent.context.current_app == "Home"


def test_message_summarization_and_notifications(phone_agent_fixture):
    agent, mock_dev = phone_agent_fixture

    # Launch Instagram & navigate to Direct Messages
    agent.launch_app("Instagram")
    agent.tap_element("Direct Messages")

    # Summarize visible messages
    msg_summary = agent.summarize_visible_messages()
    assert msg_summary["success"] is True
    assert "Super excited for the demo" in msg_summary["summary"]

    # Summarize notifications
    notif_summary = agent.get_notifications_summary()
    assert notif_summary["success"] is True
    assert notif_summary["count"] == 2
    assert "Instagram" in notif_summary["summary"]


def test_photo_search_and_safe_transfer(phone_agent_fixture):
    agent, mock_dev = phone_agent_fixture

    # 1. Search photos
    photos_res = agent.list_photos(query="hackathon")
    assert photos_res["success"] is True
    assert photos_res["count"] == 2

    # 2. Transfer file securely
    photo_id = photos_res["photos"][0]["photo_id"]
    transfer_res = agent.select_and_transfer_photo(photo_id)
    assert transfer_res["success"] is True
    assert transfer_res["filename"] == "ET_Hackathon_Winner_Team.jpg"
    assert transfer_res["local_path"] is not None


def test_social_media_safety_gate(phone_agent_fixture):
    agent, mock_dev = phone_agent_fixture

    # Stage action
    action = agent.prepare_social_action(
        action_type="comment",
        target_context="Post by Priya Sharma: 'Outstanding AI engineering architecture!'",
        payload={"text": "Thank you Priya! Built with full verification discipline."}
    )
    assert action.status == "prepared"
    assert action.action_id.startswith("soc-")

    # 1. Rejection test
    reject_res = agent.execute_social_action(action.action_id, approved=False)
    assert reject_res["success"] is False
    assert reject_res["status"] == "rejected"

    # 2. Approval test
    action2 = agent.prepare_social_action(
        action_type="like",
        target_context="Post by Priya Sharma",
        payload={}
    )
    approve_res = agent.execute_social_action(action2.action_id, approved=True)
    assert approve_res["success"] is True
    assert approve_res["status"] == "executed"
    assert approve_res["verified"] is True
