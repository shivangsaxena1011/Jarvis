"""CLI command handler for Phase 18: Cross-Device Continuity & Ambient Intelligence.

Provides operators with direct command-line control over device mesh listing, pairing,
trust revocation, task handoffs, and chunked file transfers.
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Optional

from core.devices.models import DevicePlatform, DeviceTrustState
from core.devices.orchestrator import DeviceOrchestrator


def get_cli_orchestrator() -> DeviceOrchestrator:
    return DeviceOrchestrator()


def run_device_list(trust_state: Optional[str] = None) -> int:
    orch = get_cli_orchestrator()
    filter_state = None
    if trust_state:
        try:
            filter_state = DeviceTrustState(trust_state.lower())
        except ValueError:
            pass

    devices = orch.list_devices(trust_state=filter_state)
    print("\n=== SHIVANI DEVICE MESH ===")
    print(f"Total Devices: {len(devices)}\n")
    print(f"{'DEVICE ID':<22} {'NAME':<24} {'PLATFORM':<10} {'STATUS':<12} {'STATE':<10} {'BATTERY':<8}")
    print("-" * 90)
    for d in devices:
        bat = f"{d.battery_level}%" if d.battery_level is not None else "N/A"
        online = "ONLINE" if d.is_online() else "OFFLINE"
        state = d.trust_state.value.upper()
        print(f"{d.device_id:<22} {d.display_name:<24} {d.platform:<10} {online:<12} {state:<10} {bat:<8}")
    print()
    return 0


def run_device_pair_initiate(display_name: str, platform: str = "android") -> int:
    orch = get_cli_orchestrator()
    dev_id = f"dev-{platform}-{int(time.time()) % 10000}"
    sess_id, code, sas_phrase = orch.pair_device(
        device_id=dev_id,
        display_name=display_name,
        platform=platform,
    )
    print("\n=== INITIATED DEVICE PAIRING ===")
    print(f"Device ID   : {dev_id}")
    print(f"Session ID  : {sess_id}")
    print(f"Code (PIN)  : {code}")
    print(f"SAS Words   : {sas_phrase}")
    print("\nEnter this 6-digit confirmation code on your secondary device to complete mutual pairing.\n")
    return 0


def run_device_pair_confirm(session_id: str, code: str) -> int:
    orch = get_cli_orchestrator()
    try:
        dev = orch.confirm_pairing(session_id=session_id, code=code)
        print("\n=== PAIRING CONFIRMED ===")
        print(f"Device '{dev.display_name}' ({dev.device_id}) is now TRUSTED.")
        print(f"Capabilities: {', '.join(dev.capabilities)}")
        print(f"Permissions : {', '.join(dev.permissions)}\n")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Failed to confirm pairing: {e}\n", file=sys.stderr)
        return 1


def run_device_revoke(device_id: str) -> int:
    orch = get_cli_orchestrator()
    success = orch.revoke_device(device_id)
    if success:
        print(f"\nSuccessfully revoked trust for device '{device_id}'.\n")
        return 0
    else:
        print(f"\n[ERROR] Device '{device_id}' not found.\n", file=sys.stderr)
        return 1


def run_device_handoff(task_id: str, target_device_id: str, title: str = "CLI Handoff") -> int:
    orch = get_cli_orchestrator()
    try:
        hdf = orch.initiate_handoff(
            task_id=task_id,
            title=title,
            source_device_id=orch.primary_device_id,
            target_device_id=target_device_id,
        )
        print("\n=== TASK HANDOFF INITIATED ===")
        print(f"Handoff ID : {hdf.handoff_id}")
        print(f"Task ID    : {hdf.task_id}")
        print(f"Target     : {hdf.target_device_id}")
        print(f"Status     : {hdf.status.value.upper()}\n")
        return 0
    except Exception as e:
        print(f"\n[ERROR] Handoff failed: {e}\n", file=sys.stderr)
        return 1


def run_device_transfer(file_path: str, target_device_id: str) -> int:
    orch = get_cli_orchestrator()
    try:
        tx = orch.transfer_file(
            source_device_id=orch.primary_device_id,
            target_device_id=target_device_id,
            file_path=file_path,
        )
        print("\n=== FILE TRANSFER INITIATED ===")
        print(f"Session ID : {tx.session_id}")
        print(f"File       : {tx.filename} ({tx.file_size} bytes)")
        print(f"SHA-256    : {tx.sha256_checksum}")
        print(f"Target     : {tx.target_device_id}\n")
        return 0
    except Exception as e:
        print(f"\n[ERROR] File transfer failed: {e}\n", file=sys.stderr)
        return 1


def run_device_emergency_stop() -> int:
    orch = get_cli_orchestrator()
    res = orch.emergency_stop_all(reason="CLI operator emergency stop")
    print("\n=== GLOBAL EMERGENCY STOP BROADCAST ===")
    print(f"Status  : {res['status']}")
    print(f"Affected: {', '.join(res['stopped_devices'])}\n")
    return 0


def handle_device_cli(args: argparse.Namespace) -> int:
    action = getattr(args, "device_action", "list") or "list"
    if action == "list":
        return run_device_list(trust_state=getattr(args, "state", None))
    elif action == "pair":
        if getattr(args, "confirm", False):
            return run_device_pair_confirm(
                session_id=args.session_id,
                code=args.code,
            )
        else:
            return run_device_pair_initiate(
                display_name=getattr(args, "name", "Shivani Companion"),
                platform=getattr(args, "platform", "android"),
            )
    elif action == "revoke":
        return run_device_revoke(args.device_id)
    elif action == "handoff":
        return run_device_handoff(args.task_id, args.target)
    elif action == "transfer":
        return run_device_transfer(args.file, args.target)
    elif action == "stop":
        return run_device_emergency_stop()
    else:
        print(f"Unknown device command: {action}")
        return 1
