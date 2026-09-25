"""Tests for Phase 18: Capability Discovery, Negotiation, Permission Tiers, and Task Routing."""

import os
import tempfile
import time
import pytest

from core.devices.capability_engine import CapabilityEngine
from core.devices.models import (
    ConnectionState,
    CrossDeviceCommand,
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
)
from core.devices.routing_engine import RoutingEngine
from core.devices.trust_store import TrustStore


@pytest.fixture
def mesh_setup():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    store = TrustStore(db_path=path)

    # Workstation PC
    pc = Device(
        device_id="pc-workstation",
        display_name="Workstation PC",
        platform=DevicePlatform.WINDOWS.value,
        capabilities=[
            DeviceCapability.COMPUTER_CONTROL.value,
            DeviceCapability.TERMINAL.value,
            DeviceCapability.FILES.value,
        ],
        trust_state=DeviceTrustState.TRUSTED,
        connection_state=ConnectionState.LOCAL,
        permissions=[DevicePermission.ADMIN.value],
    )
    store.upsert_device(pc)

    # Android Phone
    phone = Device(
        device_id="phone-s24",
        display_name="Galaxy S24",
        platform=DevicePlatform.ANDROID.value,
        capabilities=[
            DeviceCapability.CAMERA.value,
            DeviceCapability.UI_AUTOMATION.value,
            DeviceCapability.NOTIFICATIONS.value,
        ],
        trust_state=DeviceTrustState.TRUSTED,
        connection_state=ConnectionState.LAN,
        permissions=[DevicePermission.VIEW.value, DevicePermission.COMMAND.value],
        battery_level=80,
    )
    store.upsert_device(phone)

    yield store, pc, phone
    try:
        if os.path.exists(path):
            os.remove(path)
    except Exception:
        pass


def test_capability_negotiation(mesh_setup):
    store, pc, phone = mesh_setup
    cap_engine = CapabilityEngine(trust_store=store)

    assert set(cap_engine.discover_capabilities(pc)) == {
        DeviceCapability.COMPUTER_CONTROL.value,
        DeviceCapability.TERMINAL.value,
        DeviceCapability.FILES.value,
    }

    # Common intersection
    common = cap_engine.negotiate_capabilities(pc, phone)
    assert len(common) == 0  # Disjoint capabilities in this setup


def test_permission_tier_validation(mesh_setup):
    store, pc, phone = mesh_setup
    cap_engine = CapabilityEngine(trust_store=store)

    # Phone has VIEW and COMMAND
    assert cap_engine.check_permission(phone, DevicePermission.VIEW)
    assert cap_engine.check_permission(phone, DevicePermission.COMMAND)
    # Phone does NOT have CONTROL or ADMIN
    assert not cap_engine.check_permission(phone, DevicePermission.CONTROL)
    assert not cap_engine.check_permission(phone, DevicePermission.ADMIN)

    # PC has ADMIN -> has everything
    assert cap_engine.check_permission(pc, DevicePermission.VIEW)
    assert cap_engine.check_permission(pc, DevicePermission.CONTROL)
    assert cap_engine.check_permission(pc, DevicePermission.ADMIN)


def test_anti_replay_and_command_validation(mesh_setup):
    store, pc, phone = mesh_setup
    cap_engine = CapabilityEngine(trust_store=store, max_timestamp_skew_sec=10.0)

    # 1. Valid command from PC to Phone: launch_app (PC is ADMIN, phone has UI_AUTOMATION)
    cmd = CrossDeviceCommand(
        source_device_id="pc-workstation",
        target_device_id="phone-s24",
        action="launch_app",
        timestamp=time.time(),
        nonce="nonce-1",
    )
    valid, err = cap_engine.validate_command(cmd)
    assert valid
    assert err is None

    # 2. Replay attack: same nonce
    valid_replay, err_replay = cap_engine.validate_command(cmd)
    assert not valid_replay
    assert "Replay attack detected" in err_replay

    # 3. Timestamp skew attack (100 seconds in the past)
    stale_cmd = CrossDeviceCommand(
        source_device_id="pc-workstation",
        target_device_id="phone-s24",
        action="launch_app",
        timestamp=time.time() - 100.0,
        nonce="nonce-2",
    )
    valid_stale, err_stale = cap_engine.validate_command(stale_cmd)
    assert not valid_stale
    assert "skewed" in err_stale

    # 4. Privilege escalation: Phone attempting CONTROL action on PC
    illegal_cmd = CrossDeviceCommand(
        source_device_id="phone-s24",
        target_device_id="pc-workstation",
        action="desktop_click",  # requires CONTROL
        timestamp=time.time(),
        nonce="nonce-3",
    )
    valid_illegal, err_illegal = cap_engine.validate_command(illegal_cmd)
    assert not valid_illegal
    assert "lacks required permission" in err_illegal


def test_task_routing_decisions(mesh_setup):
    store, pc, phone = mesh_setup
    router = RoutingEngine(trust_store=store, default_primary_device_id="pc-workstation")

    # Routing camera task -> should route to phone
    res_camera = router.route_task("Take a quick selfie and save photo")
    assert res_camera.selected_device_id == "phone-s24"
    assert res_camera.target_platform == DevicePlatform.ANDROID.value

    # Routing terminal/code task -> should route to workstation PC
    res_code = router.route_task("Run pytest in terminal to verify test suite")
    assert res_code.selected_device_id == "pc-workstation"
    assert res_code.target_platform == DevicePlatform.WINDOWS.value

    # Active device election
    elected = router.elect_active_device()
    assert elected is not None
    assert elected.device_id in ("pc-workstation", "phone-s24")
