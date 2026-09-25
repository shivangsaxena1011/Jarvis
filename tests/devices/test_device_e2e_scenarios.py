"""End-to-End Scenario Verification for Phase 18: Cross-Device Continuity & Ambient Intelligence.

Covers all 8 key real-world scenarios:
1. File handoff PC -> Android with SHA-256 integrity verification
2. Task continuation Android -> PC ("continue what I was doing on my phone")
3. Remote computer action triggered from Android companion
4. Disconnect & reconnect recovery with heartbeat
5. Rogue device revocation & blocked access enforcement
6. Global emergency stop broadcast across all nodes
7. State conflict resolution & active device election
8. Ambient privacy boundary & zero-surveillance enforcement
"""

import os
import tempfile
import time
import pytest

from core.devices.mock_network import MockNetworkEnvironment
from core.devices.models import (
    AmbientContextState,
    ConnectionState,
    CrossDeviceCommand,
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
    HandoffStatus,
    HandoffType,
    TransferStatus,
)


@pytest.fixture
def mesh_env():
    env = MockNetworkEnvironment()
    yield env
    env.cleanup()


# -----------------------------------------------------------------------------
# Scenario 1: File Handoff PC -> Android
# -----------------------------------------------------------------------------
def test_scenario_1_file_handoff_pc_to_phone(mesh_env):
    """'Shivani, send this presentation to my phone.'"""
    orch = mesh_env.orchestrator

    # Create dummy presentation file
    pres_path = os.path.join(mesh_env.temp_dir, "Quarterly_Pitch.pptx")
    test_content = b"PPTX_PRESENTATION_SLIDE_DATA_CONTENT_" * 1024
    with open(pres_path, "wb") as f:
        f.write(test_content)

    # Execute full chunked file transfer
    dest_dir = os.path.join(mesh_env.temp_dir, "phone_storage")
    session, out_file = mesh_env.simulate_full_file_transfer(
        source_id="pc-workstation-001",
        target_id="phone-galaxy-001",
        file_path=pres_path,
        destination_dir=dest_dir,
    )

    assert session.status == TransferStatus.COMPLETED
    assert session.progress_percentage == 100.0
    assert os.path.exists(out_file)

    with open(out_file, "rb") as f:
        assert f.read() == test_content


# -----------------------------------------------------------------------------
# Scenario 2: Task Continuation Android -> PC
# -----------------------------------------------------------------------------
def test_scenario_2_task_continuation_phone_to_pc(mesh_env):
    """'Shivani, continue what I was doing on my phone.'"""
    orch = mesh_env.orchestrator

    # User was reading a draft proposal on their phone
    phone_context = {
        "task_id": "task-proposal-99",
        "title": "Autonomous AI Strategy Proposal",
        "current_step": 4,
        "total_steps": 10,
        "active_url": "https://company.docs/strategy-proposal",
        "summary": "Reviewed section 3 on desktop autonomy.",
    }

    hdf = orch.initiate_handoff(
        task_id="task-proposal-99",
        title="Resume Proposal Draft",
        source_device_id="phone-galaxy-001",
        target_device_id="pc-workstation-001",
        handoff_type=HandoffType.CONTINUE,
        context_payload=phone_context,
    )

    assert hdf.status == HandoffStatus.INITIATED

    # PC accepts and resumes task
    accepted = orch.accept_handoff(hdf.handoff_id, "pc-workstation-001")
    assert accepted.status == HandoffStatus.IN_PROGRESS
    assert accepted.context_payload["active_url"] == "https://company.docs/strategy-proposal"

    # PC completes draft and marks handoff done
    completed = orch.complete_handoff(
        hdf.handoff_id,
        result_payload={"summary": "Document finished and exported to PDF.", "pages": 14},
    )
    assert completed.status == HandoffStatus.COMPLETED
    assert completed.result_payload["pages"] == 14


# -----------------------------------------------------------------------------
# Scenario 3: Remote Computer Action Triggered from Mobile Companion
# -----------------------------------------------------------------------------
def test_scenario_3_remote_computer_action_from_phone(mesh_env):
    """Phone requests PC to run an authorized action."""
    orch = mesh_env.orchestrator

    cmd = CrossDeviceCommand(
        source_device_id="phone-galaxy-001",
        target_device_id="pc-workstation-001",
        action="launch_app",
        parameters={"app_name": "notepad"},
        timestamp=time.time(),
        nonce="cmd-remote-001",
    )

    res = orch.execute_remote_command(cmd)
    assert res["success"]
    assert "dispatched" in res["message"]


# -----------------------------------------------------------------------------
# Scenario 4: Disconnect & Reconnect Recovery
# -----------------------------------------------------------------------------
def test_scenario_4_disconnect_and_reconnect(mesh_env):
    """Network drop and automated reconnect recovery."""
    orch = mesh_env.orchestrator

    # Verify initially online
    phone = orch.get_device("phone-galaxy-001")
    assert phone.is_online()

    # Disconnect
    mesh_env.simulate_disconnect("phone-galaxy-001")
    assert not orch.get_device("phone-galaxy-001").is_online()

    # Reconnect
    mesh_env.simulate_reconnect("phone-galaxy-001")
    reconnected = orch.get_device("phone-galaxy-001")
    assert reconnected.is_online()
    assert reconnected.connection_state == ConnectionState.LAN


# -----------------------------------------------------------------------------
# Scenario 5: Rogue Device Revocation & Blocked Access
# -----------------------------------------------------------------------------
def test_scenario_5_rogue_device_revocation_and_blocking(mesh_env):
    """Rogue device attempts unauthorized access; blocked and rejected."""
    orch = mesh_env.orchestrator

    # Rogue device discovered
    rogue = Device(
        device_id="rogue-laptop-666",
        display_name="Untrusted Rogue Machine",
        platform=DevicePlatform.LAPTOP.value,
        trust_state=DeviceTrustState.DISCOVERED,
    )
    orch.trust_store.upsert_device(rogue)

    # Command from un-trusted device must be rejected
    cmd = CrossDeviceCommand(
        source_device_id="rogue-laptop-666",
        target_device_id="pc-workstation-001",
        action="launch_app",
        timestamp=time.time(),
        nonce="rogue-001",
    )
    valid, err = orch.capability.validate_command(cmd)
    assert not valid
    assert "not TRUSTED" in err

    # Block device
    assert orch.block_device("rogue-laptop-666")
    assert orch.get_device("rogue-laptop-666").trust_state == DeviceTrustState.BLOCKED


# -----------------------------------------------------------------------------
# Scenario 6: Global Emergency Stop Broadcast
# -----------------------------------------------------------------------------
def test_scenario_6_global_emergency_stop_broadcast(mesh_env):
    """'Shivani, stop everything immediately across all devices!'"""
    orch = mesh_env.orchestrator

    emergency_received = []
    orch.register_emergency_callback(lambda reason: emergency_received.append(reason))

    res = orch.emergency_stop_all(reason="User emergency panic stop")
    assert res["status"] == "ABORTED_ALL"
    assert len(res["stopped_devices"]) >= 3
    assert len(emergency_received) == 1
    assert emergency_received[0] == "User emergency panic stop"


# -----------------------------------------------------------------------------
# Scenario 7: State Conflict Resolution & Active Device Election
# -----------------------------------------------------------------------------
def test_scenario_7_election_and_routing(mesh_env):
    """Multi-device presence and automated task routing."""
    orch = mesh_env.orchestrator

    # Elect active device (PC and phone both online)
    elected = orch.routing.elect_active_device()
    assert elected is not None
    assert elected.device_id in ("pc-workstation-001", "phone-galaxy-001", "laptop-travel-001")

    # Record user interaction on phone -> phone becomes active
    orch.routing.record_interaction("phone-galaxy-001")
    assert orch.routing.active_device_id == "phone-galaxy-001"


# -----------------------------------------------------------------------------
# Scenario 8: Ambient Privacy Boundary & Zero-Surveillance Enforcement
# -----------------------------------------------------------------------------
def test_scenario_8_ambient_privacy_and_zero_surveillance(mesh_env):
    """Verifies that no hidden sensor data collection is ever permitted."""
    orch = mesh_env.orchestrator

    # 1. Background sensor access strictly blocked
    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        orch.ambient.verify_sensor_access("microphone", explicit_user_intent=False)

    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        orch.ambient.verify_sensor_access("camera", explicit_user_intent=False)

    with pytest.raises(PermissionError, match="Zero-surveillance guarantee"):
        orch.ambient.verify_sensor_access("screen_recorder", explicit_user_intent=False)

    # 2. Explicit clipboard sync with secret token masking
    clip_result = orch.sync_clipboard(
        source_device_id="pc-workstation-001",
        target_device_id="phone-galaxy-001",
        text="Token: ghp_123456789012345678901234567890123456",
        explicit=True,
    )
    assert clip_result["success"]
    assert clip_result["was_redacted"]
    assert "***REDACTED_CREDENTIAL***" in clip_result["payload"]
