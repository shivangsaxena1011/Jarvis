"""Tests for Phase 18: Ambient Intelligence Privacy Boundaries & Zero-Surveillance Enforcement."""

import os
import tempfile
import pytest

from core.devices.ambient_engine import AmbientEngine
from core.devices.models import (
    AmbientContextState,
    Device,
    DeviceTrustState,
)
from core.devices.trust_store import TrustStore


@pytest.fixture
def ambient_setup():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = TrustStore(db_path=path)

    pc = Device(
        device_id="pc-main",
        display_name="Main PC",
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(pc)

    phone = Device(
        device_id="phone-main",
        display_name="Main Phone",
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(phone)

    engine = AmbientEngine(trust_store=store)

    yield store, pc, phone, engine
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_zero_surveillance_covert_access_blocked(ambient_setup):
    store, pc, phone, engine = ambient_setup

    # 1. Background microphone access without explicit intent must be blocked
    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        engine.verify_sensor_access("microphone", explicit_user_intent=False)

    # 2. Covert camera capture must be blocked
    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        engine.verify_sensor_access("camera", explicit_user_intent=False)

    # 3. Covert background screen recording must be blocked
    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        engine.verify_sensor_access("screen_recorder", explicit_user_intent=False)

    # 4. Explicit user intent allows access
    assert engine.verify_sensor_access("microphone", explicit_user_intent=True)
    assert engine.verify_sensor_access("camera", explicit_user_intent=True)


def test_ambient_state_modes(ambient_setup):
    store, pc, phone, engine = ambient_setup

    engine.set_ambient_state(AmbientContextState.OFF)
    assert engine.get_ambient_state() == AmbientContextState.OFF

    # In OFF mode, even ambient sensors without explicit intent return False
    assert not engine.verify_sensor_access("ambient_light", explicit_user_intent=False)

    engine.set_ambient_state(AmbientContextState.PROJECT)
    assert engine.get_ambient_state() == AmbientContextState.PROJECT


def test_explicit_clipboard_sharing_and_credential_masking(ambient_setup):
    store, pc, phone, engine = ambient_setup

    # 1. Background (non-explicit) clipboard access must be rejected
    with pytest.raises(PermissionError, match="requires explicit user trigger"):
        engine.share_clipboard("pc-main", "phone-main", "Hello from PC", explicit_user_action=False)

    # 2. Normal text sharing
    res = engine.share_clipboard("pc-main", "phone-main", "https://github.com/project", explicit_user_action=True)
    assert res["success"]
    assert res["payload"] == "https://github.com/project"
    assert not res["was_redacted"]

    # 3. Sharing API key or secret must be masked/redacted for safety
    secret_text = "Here is my secret token: sk-ant-api03-abcdef1234567890abcdef1234567890"
    res_secret = engine.share_clipboard("pc-main", "phone-main", secret_text, explicit_user_action=True)
    assert res_secret["success"]
    assert res_secret["was_redacted"]
    assert "***REDACTED_CREDENTIAL***" in res_secret["payload"]

    # 4. Audit trail reflects operations
    audit = engine.get_audit_trail()
    assert len(audit) >= 2
    assert any(a["event"] == "clipboard_shared" for a in audit)
