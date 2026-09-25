"""Tests for Phase 18: Device Trust Store, Pairing Handshake, and SAS Verification."""

import os
import tempfile
import time
import pytest

from core.devices.models import (
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
)
from core.devices.pairing_engine import PairingEngine
from core.devices.trust_store import TrustStore


@pytest.fixture
def temp_trust_store():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = TrustStore(db_path=path)
    yield store
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_trust_store_crud(temp_trust_store):
    dev = Device(
        device_id="phone-test-1",
        display_name="Test Phone",
        platform=DevicePlatform.ANDROID.value,
        capabilities=[DeviceCapability.CAMERA.value, DeviceCapability.NOTIFICATIONS.value],
        trust_state=DeviceTrustState.DISCOVERED,
        battery_level=75,
    )
    temp_trust_store.upsert_device(dev)

    fetched = temp_trust_store.get_device("phone-test-1")
    assert fetched is not None
    assert fetched.display_name == "Test Phone"
    assert fetched.battery_level == 75
    assert fetched.trust_state == DeviceTrustState.DISCOVERED

    # Update trust state
    assert temp_trust_store.update_trust_state("phone-test-1", DeviceTrustState.TRUSTED)
    assert temp_trust_store.get_device("phone-test-1").trust_state == DeviceTrustState.TRUSTED

    # List devices
    devs = temp_trust_store.list_devices(DeviceTrustState.TRUSTED)
    assert len(devs) == 1
    assert devs[0].device_id == "phone-test-1"


def test_pairing_handshake_success(temp_trust_store):
    engine = PairingEngine(trust_store=temp_trust_store, code_ttl_sec=300)

    # 1. Initiate pairing
    session_id, code, sas = engine.initiate_pairing(
        device_id="phone-alpha",
        display_name="Alpha Phone",
        platform="android",
    )
    assert len(code) == 6
    assert code.isdigit()
    assert "-" in sas

    # Verify device is recorded in PAIRING state
    dev = temp_trust_store.get_device("phone-alpha")
    assert dev.trust_state == DeviceTrustState.PAIRING

    # 2. Confirm pairing with valid code
    paired_dev = engine.confirm_pairing(
        session_id=session_id,
        code_attempt=code,
        capabilities=["notifications", "camera"],
    )
    assert paired_dev.trust_state == DeviceTrustState.TRUSTED
    assert paired_dev.auth_token is not None
    assert paired_dev.has_permission(DevicePermission.VIEW)

    # Verify token check
    assert engine.verify_auth_token("phone-alpha", paired_dev.auth_token)
    assert not engine.verify_auth_token("phone-alpha", "wrong-token")


def test_pairing_invalid_code_rejected(temp_trust_store):
    engine = PairingEngine(trust_store=temp_trust_store, code_ttl_sec=300)
    session_id, code, _ = engine.initiate_pairing("phone-beta", "Beta Phone", "android")

    with pytest.raises(ValueError, match="Invalid pairing code"):
        engine.confirm_pairing(session_id, "000000" if code != "000000" else "111111")


def test_pairing_expired_session(temp_trust_store):
    engine = PairingEngine(trust_store=temp_trust_store, code_ttl_sec=0.01)
    session_id, code, _ = engine.initiate_pairing("phone-gamma", "Gamma Phone", "android")
    time.sleep(0.02)

    with pytest.raises(TimeoutError, match="expired"):
        engine.confirm_pairing(session_id, code)


def test_revocation_and_blocking(temp_trust_store):
    engine = PairingEngine(trust_store=temp_trust_store)
    session_id, code, _ = engine.initiate_pairing("phone-delta", "Delta Phone", "android")
    dev = engine.confirm_pairing(session_id, code)
    token = dev.auth_token

    assert engine.verify_auth_token("phone-delta", token)

    # Revoke trust
    assert engine.revoke_device("phone-delta")
    assert not engine.verify_auth_token("phone-delta", token)
    revoked = temp_trust_store.get_device("phone-delta")
    assert revoked.trust_state == DeviceTrustState.REVOKED

    # Block device
    assert engine.block_device("phone-delta")
    blocked = temp_trust_store.get_device("phone-delta")
    assert blocked.trust_state == DeviceTrustState.BLOCKED

    # Attempt to pair blocked device should fail
    with pytest.raises(PermissionError, match="BLOCKED"):
        engine.initiate_pairing("phone-delta", "Delta Phone", "android")

    # Unblock
    assert engine.unblock_device("phone-delta")
    unblocked = temp_trust_store.get_device("phone-delta")
    assert unblocked.trust_state == DeviceTrustState.DISCOVERED
