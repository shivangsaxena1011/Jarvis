"""Tests for Phase 18: Cross-Device Task Handoffs and Minimal Context Packaging."""

import os
import tempfile
import time
import pytest

from core.devices.handoff_engine import HandoffEngine
from core.devices.models import (
    Device,
    DevicePlatform,
    DeviceTrustState,
    HandoffStatus,
    HandoffType,
)
from core.devices.trust_store import TrustStore


@pytest.fixture
def handoff_setup():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = TrustStore(db_path=path)

    pc = Device(
        device_id="pc-node",
        display_name="Desktop PC",
        platform=DevicePlatform.WINDOWS.value,
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(pc)

    phone = Device(
        device_id="phone-node",
        display_name="Mobile Phone",
        platform=DevicePlatform.ANDROID.value,
        trust_state=DeviceTrustState.TRUSTED,
    )
    store.upsert_device(phone)

    yield store, pc, phone
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_handoff_lifecycle_continue(handoff_setup):
    store, pc, phone = handoff_setup
    engine = HandoffEngine(trust_store=store)

    # 1. Create handoff from PC to Phone
    context = {
        "task_id": "task-research-42",
        "title": "Autonomous paper research",
        "current_step": 3,
        "total_steps": 5,
        "active_url": "https://arxiv.org/abs/2401.00000",
        "auth_token": "SENSITIVE_SECRET_DO_NOT_LEAK",  # should be scrubbed
    }

    hdf = engine.create_handoff(
        task_id="task-research-42",
        title="Research Paper Handoff",
        source_device_id="pc-node",
        target_device_id="phone-node",
        handoff_type=HandoffType.CONTINUE,
        context_payload=context,
    )

    assert hdf.status == HandoffStatus.INITIATED
    assert hdf.context_payload["active_url"] == "https://arxiv.org/abs/2401.00000"
    assert "auth_token" not in hdf.context_payload  # Scrubbed

    # 2. Accept handoff on phone
    accepted = engine.accept_handoff(hdf.handoff_id, "phone-node")
    assert accepted.status == HandoffStatus.IN_PROGRESS

    # 3. Complete handoff with results
    result_data = {"summary": "Paper reviewed on mobile device.", "status": "DONE"}
    completed = engine.complete_handoff(hdf.handoff_id, result_data)
    assert completed.status == HandoffStatus.COMPLETED
    assert completed.result_payload == result_data


def test_handoff_wrong_device_rejection(handoff_setup):
    store, pc, phone = handoff_setup
    engine = HandoffEngine(trust_store=store)

    hdf = engine.create_handoff(
        task_id="task-10",
        title="Test Handoff",
        source_device_id="pc-node",
        target_device_id="phone-node",
    )

    # Attempting to accept from pc-node should fail
    with pytest.raises(PermissionError, match="not the intended target"):
        engine.accept_handoff(hdf.handoff_id, "pc-node")


def test_handoff_expiration(handoff_setup):
    store, pc, phone = handoff_setup
    engine = HandoffEngine(trust_store=store, default_ttl_sec=0.01)

    hdf = engine.create_handoff(
        task_id="task-expire",
        title="Expired Handoff",
        source_device_id="pc-node",
        target_device_id="phone-node",
        ttl_sec=0.01,
    )
    time.sleep(0.02)

    with pytest.raises(TimeoutError, match="expired"):
        engine.accept_handoff(hdf.handoff_id, "phone-node")
