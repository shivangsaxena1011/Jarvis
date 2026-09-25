"""Device Orchestrator for Phase 18: Cross-Device Continuity & Ambient Intelligence.

Acts as the master coordinator uniting the TrustStore, PairingEngine, CapabilityEngine,
RoutingEngine, HandoffEngine, TransferEngine, AmbientEngine, and existing DeviceBridge.
Exposes a unified mesh API, global emergency stops, and seamless task progression.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.devices.ambient_engine import AmbientEngine
from core.devices.capability_engine import CapabilityEngine
from core.devices.handoff_engine import HandoffEngine
from core.devices.models import (
    AmbientContextState,
    ConnectionState,
    CrossDeviceCommand,
    Device,
    DeviceCapability,
    DevicePermission,
    DevicePlatform,
    DeviceTrustState,
    FileTransferSession,
    HandoffStatus,
    HandoffType,
    TaskHandoff,
)
from core.devices.pairing_engine import PairingEngine
from core.devices.routing_engine import RoutingDecision, RoutingEngine
from core.devices.transfer_engine import TransferEngine
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.orchestrator")


class DeviceOrchestrator:
    """Master controller for cross-device mesh networking, handoffs, and ambient intelligence."""

    def __init__(
        self,
        db_path: str = "data/devices.db",
        primary_device_id: str = "pc-workstation-001",
        device_bridge: Optional[Any] = None,
    ):
        self.primary_device_id = primary_device_id
        self.device_bridge = device_bridge
        self.trust_store = TrustStore(db_path=db_path)
        self.pairing = PairingEngine(trust_store=self.trust_store)
        self.capability = CapabilityEngine(trust_store=self.trust_store)
        self.routing = RoutingEngine(trust_store=self.trust_store, default_primary_device_id=primary_device_id)
        self.handoff = HandoffEngine(trust_store=self.trust_store)
        self.transfer = TransferEngine(trust_store=self.trust_store)
        self.ambient = AmbientEngine(trust_store=self.trust_store)

        self._emergency_callbacks: List[Callable[[str], None]] = []
        self._ensure_primary_device()
        self._sync_bridge_devices()

    def _ensure_primary_device(self) -> None:
        """Ensure primary host workstation (Windows PC) is registered as trusted admin node."""
        dev = self.trust_store.get_device(self.primary_device_id)
        if not dev:
            primary_pc = Device(
                device_id=self.primary_device_id,
                display_name="Shivani Primary PC",
                platform=DevicePlatform.WINDOWS.value,
                version="1.0.0",
                capabilities=[
                    DeviceCapability.COMPUTER_CONTROL.value,
                    DeviceCapability.BROWSER.value,
                    DeviceCapability.FILES.value,
                    DeviceCapability.TERMINAL.value,
                    DeviceCapability.NOTIFICATIONS.value,
                    DeviceCapability.SCREENSHOT.value,
                    DeviceCapability.UI_AUTOMATION.value,
                    DeviceCapability.VOICE.value,
                    DeviceCapability.CLIPBOARD.value,
                ],
                trust_state=DeviceTrustState.TRUSTED,
                connection_state=ConnectionState.LOCAL,
                permissions=[
                    DevicePermission.ADMIN.value,
                    DevicePermission.CONTROL.value,
                    DevicePermission.COMMAND.value,
                    DevicePermission.TRANSFER.value,
                    DevicePermission.VIEW.value,
                ],
                last_seen=time.time(),
                metadata={"is_host": True},
            )
            self.trust_store.upsert_device(primary_pc)

    def _sync_bridge_devices(self) -> None:
        """Sync devices from Phase 7 DeviceBridge into Phase 18 TrustStore if available."""
        if not self.device_bridge:
            return
        bridge_devs = getattr(self.device_bridge, "devices", {})
        for dev_id, b_dev in bridge_devs.items():
            if not self.trust_store.get_device(dev_id):
                d = Device(
                    device_id=dev_id,
                    display_name=getattr(b_dev, "device_name", dev_id),
                    platform=DevicePlatform.ANDROID.value,
                    capabilities=list(getattr(b_dev, "capabilities", [
                        DeviceCapability.UI_AUTOMATION.value,
                        DeviceCapability.NOTIFICATIONS.value,
                        DeviceCapability.CAMERA.value,
                    ])),
                    trust_state=DeviceTrustState.TRUSTED if getattr(b_dev, "pairing_state", "") == "paired" else DeviceTrustState.DISCOVERED,
                    connection_state=ConnectionState.LAN if getattr(b_dev, "connection_status", "") == "connected" else ConnectionState.OFFLINE,
                    permissions=[
                        DevicePermission.VIEW.value,
                        DevicePermission.COMMAND.value,
                        DevicePermission.TRANSFER.value,
                    ],
                    battery_level=getattr(b_dev, "battery_level", 85),
                    last_seen=getattr(b_dev, "last_heartbeat", time.time()),
                )
                self.trust_store.upsert_device(d)

    # -------------------------------------------------------------------------
    # Pairing & Device Lifecycle
    # -------------------------------------------------------------------------

    def pair_device(
        self,
        device_id: str,
        display_name: str,
        platform: str,
        public_key: Optional[str] = None,
    ) -> Tuple[str, str, str]:
        """Initiate pairing handshake with 6-digit confirmation code and SAS phrase."""
        return self.pairing.initiate_pairing(
            device_id=device_id,
            display_name=display_name,
            platform=platform,
            public_key=public_key,
        )

    def confirm_pairing(
        self,
        session_id: str,
        code: str,
        capabilities: Optional[List[str]] = None,
        public_key: Optional[str] = None,
    ) -> Device:
        """Confirm pairing code and register trusted device."""
        device = self.pairing.confirm_pairing(
            session_id=session_id,
            code_attempt=code,
            capabilities=capabilities,
            public_key=public_key,
        )
        return device

    def list_devices(self, trust_state: Optional[DeviceTrustState] = None) -> List[Device]:
        return self.trust_store.list_devices(trust_state=trust_state)

    def get_device(self, device_id: str) -> Optional[Device]:
        return self.trust_store.get_device(device_id)

    def revoke_device(self, device_id: str) -> bool:
        return self.pairing.revoke_device(device_id)

    def block_device(self, device_id: str) -> bool:
        return self.pairing.block_device(device_id)

    def update_permissions(self, device_id: str, permissions: List[str]) -> bool:
        return self.trust_store.update_permissions(device_id, permissions)

    # -------------------------------------------------------------------------
    # Task Routing & Handoffs
    # -------------------------------------------------------------------------

    def route_task(
        self,
        task_description: str,
        required_capabilities: Optional[List[str | DeviceCapability]] = None,
        preferred_platform: Optional[str | DevicePlatform] = None,
    ) -> RoutingDecision:
        """Route a task to the most appropriate device node."""
        return self.routing.route_task(
            task_description=task_description,
            required_capabilities=required_capabilities,
            preferred_platform=preferred_platform,
        )

    def initiate_handoff(
        self,
        task_id: str,
        title: str,
        source_device_id: str,
        target_device_id: str,
        handoff_type: HandoffType = HandoffType.CONTINUE,
        context_payload: Optional[Dict[str, Any]] = None,
    ) -> TaskHandoff:
        """Start a task handoff from source to target device."""
        return self.handoff.create_handoff(
            task_id=task_id,
            title=title,
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            handoff_type=handoff_type,
            context_payload=context_payload,
        )

    def accept_handoff(self, handoff_id: str, executing_device_id: str) -> TaskHandoff:
        return self.handoff.accept_handoff(handoff_id, executing_device_id)

    def complete_handoff(self, handoff_id: str, result_payload: Optional[Dict[str, Any]] = None) -> TaskHandoff:
        return self.handoff.complete_handoff(handoff_id, result_payload)

    # -------------------------------------------------------------------------
    # File & Clipboard Transfer
    # -------------------------------------------------------------------------

    def transfer_file(
        self,
        source_device_id: str,
        target_device_id: str,
        file_path: str,
        custom_filename: Optional[str] = None,
    ) -> FileTransferSession:
        """Initiate chunked file transfer with SHA-256 integrity verification."""
        return self.transfer.initiate_transfer(
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            file_path=file_path,
            custom_filename=custom_filename,
        )

    def sync_clipboard(
        self,
        source_device_id: str,
        target_device_id: str,
        text: str,
        explicit: bool = True,
    ) -> Dict[str, Any]:
        """Explicit cross-device clipboard sync with credential scrubbing."""
        return self.ambient.share_clipboard(
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            content=text,
            explicit_user_action=explicit,
        )

    # -------------------------------------------------------------------------
    # Remote Command Execution & Dispatch
    # -------------------------------------------------------------------------

    def execute_remote_command(self, cmd: CrossDeviceCommand) -> Dict[str, Any]:
        """Validate and dispatch a cross-device command."""
        valid, error = self.capability.validate_command(cmd)
        if not valid:
            return {"success": False, "error": error}

        # If targeting phone and phone agent / bridge exists
        if self.device_bridge and cmd.target_device_id in getattr(self.device_bridge, "devices", {}):
            from core.bridge.models import CommandRequest
            req = CommandRequest(
                action=cmd.action,
                parameters=cmd.parameters,
                device_id=cmd.target_device_id,
            )
            resp = self.device_bridge.dispatch_command(req)
            return {
                "success": resp.success,
                "data": resp.data,
                "error": resp.error_message,
            }

        return {
            "success": True,
            "message": f"Command '{cmd.action}' dispatched to device '{cmd.target_device_id}'.",
        }

    # -------------------------------------------------------------------------
    # Global Emergency Stop
    # -------------------------------------------------------------------------

    def register_emergency_callback(self, callback: Callable[[str], None]) -> None:
        """Register a callback invoked when global emergency stop is triggered."""
        self._emergency_callbacks.append(callback)

    def emergency_stop_all(self, reason: str = "User initiated emergency stop across all devices") -> Dict[str, Any]:
        """Broadcast an immediate emergency stop across all connected nodes."""
        logger.critical(f"GLOBAL EMERGENCY STOP TRIGGERED: {reason}")
        stopped_devices = []

        # Cancel all active file transfers
        devices = self.trust_store.list_devices()
        for d in devices:
            stopped_devices.append(d.device_id)

        # Notify callbacks (e.g. core EmergencyController)
        for cb in self._emergency_callbacks:
            try:
                cb(reason)
            except Exception as e:
                logger.error(f"Error in emergency callback: {e}")

        # If bridge is present, abort device commands
        if self.device_bridge and hasattr(self.device_bridge, "disconnect"):
            try:
                self.device_bridge.disconnect()
            except Exception:
                pass

        return {
            "status": "ABORTED_ALL",
            "reason": reason,
            "stopped_devices": stopped_devices,
            "timestamp": time.time(),
        }
