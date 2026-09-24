"""Tests for SHIVANI Secure Device Bridge and Cryptographic Protocol."""

import pytest
import time
from core.bridge.device_bridge import DeviceBridge
from core.bridge.mock_device import MockAndroidDevice
from core.bridge.models import CommandRequest, DeviceIdentity
from core.bridge.crypto import generate_pairing_code, generate_device_token, sign_payload, verify_signature


def test_crypto_helpers():
    code = generate_pairing_code()
    assert len(code) == 6
    assert code.isdigit()

    token = generate_device_token("shivani-android-001")
    assert len(token) == 64

    sig = sign_payload("test_payload", "secret_key_123")
    assert verify_signature("test_payload", "secret_key_123", sig) is True
    assert verify_signature("test_payload", "wrong_key", sig) is False


def test_device_bridge_pairing_lifecycle():
    bridge = DeviceBridge(heartbeat_timeout_sec=5.0)

    # 1. Start pairing session
    session_id, code = bridge.start_pairing(device_name="Pixel 9 Pro")
    assert session_id.startswith("pair-")
    assert len(code) == 6

    # 2. Reject incorrect pairing code
    with pytest.raises(ValueError, match="Invalid pairing code"):
        bridge.confirm_pairing(
            session_id=session_id,
            challenge_code="000000",
            device_id="pixel-001",
            device_name="Pixel 9 Pro"
        )

    # 3. Approve with correct code
    dev = bridge.confirm_pairing(
        session_id=session_id,
        challenge_code=code,
        device_id="pixel-001",
        device_name="Pixel 9 Pro"
    )
    assert dev.device_id == "pixel-001"
    assert dev.pairing_state == "paired"
    assert dev.connection_status == "connected"
    assert dev.auth_token is not None
    assert bridge.is_connected("pixel-001") is True


def test_device_bridge_heartbeat_and_disconnect():
    bridge = DeviceBridge(heartbeat_timeout_sec=0.2)
    dev = DeviceIdentity(
        device_id="test-phone-01",
        device_name="Test Phone",
        pairing_state="paired",
        connection_status="connected",
        last_seen=time.time()
    )
    bridge.register_paired_device(dev)
    assert bridge.is_connected("test-phone-01") is True

    # Allow heartbeat timeout to expire
    time.sleep(0.3)
    assert bridge.is_connected("test-phone-01") is False

    # Send heartbeat ping to revive
    assert bridge.heartbeat("test-phone-01") is True
    assert bridge.is_connected("test-phone-01") is True

    # Explicit disconnect
    bridge.disconnect("test-phone-01")
    assert bridge.is_connected("test-phone-01") is False


def test_device_bridge_command_dispatch_and_mock_device():
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

    # Send status query
    cmd = CommandRequest(
        device_id="shivani-android-001",
        action="get_device_status"
    )
    resp = bridge.send_command(cmd)
    assert resp.success is True
    assert resp.request_id == cmd.request_id
    assert resp.result["battery_level"] == 88
    assert resp.result["permissions"]["accessibility"] is True

    # Test emergency stop cancellation propagation
    cancel_resp = bridge.cancel_current_task("shivani-android-001")
    assert cancel_resp.success is True
    assert mock_dev.is_task_cancelled is True
