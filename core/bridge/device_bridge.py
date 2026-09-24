"""Secure Device Bridge for SHIVANI.

Manages paired Android device identities, secure authentication, heartbeat monitoring,
and structured command dispatch with correlation IDs and cancellation support.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.bridge.models import CommandRequest, CommandResponse, DeviceIdentity
from core.bridge.crypto import generate_pairing_code, generate_device_token

logger = logging.getLogger("shivani.bridge")


class DeviceBridge:
    """Manages communication between SHIVANI Core and paired Android devices."""

    def __init__(self, heartbeat_timeout_sec: float = 30.0):
        self.heartbeat_timeout_sec = heartbeat_timeout_sec
        self.devices: Dict[str, DeviceIdentity] = {}
        self.active_device_id: Optional[str] = None
        self._pending_pairing_sessions: Dict[str, Dict[str, Any]] = {}
        self._transport_handler: Optional[Callable[[CommandRequest], CommandResponse]] = None
        self._event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

    def register_transport_handler(self, handler: Callable[[CommandRequest], CommandResponse]) -> None:
        """Register a network or mock transport handler for executing commands."""
        self._transport_handler = handler

    def add_event_listener(self, listener: Callable[[str, Dict[str, Any]], None]) -> None:
        """Register a callback for asynchronous events received from devices."""
        self._event_listeners.append(listener)

    # -------------------------------------------------------------------------
    # Pairing & Identity Management
    # -------------------------------------------------------------------------

    def start_pairing(self, device_name: str = "Shivani Phone") -> Tuple[str, str]:
        """Initiate device pairing by generating a high-entropy 6-digit challenge.

        Returns:
            Tuple of (session_id, pairing_code).
        """
        pairing_code = generate_pairing_code()
        session_id = f"pair-{int(time.time())}-{pairing_code[:3]}"
        self._pending_pairing_sessions[session_id] = {
            "pairing_code": pairing_code,
            "device_name": device_name,
            "created_at": time.time(),
            "expires_at": time.time() + 300,  # 5 minutes expiry
        }
        logger.info(f"Initiated pairing session {session_id} with challenge code: {pairing_code}")
        return session_id, pairing_code

    def confirm_pairing(
        self,
        session_id: str,
        challenge_code: str,
        device_id: str,
        device_name: str = "Shivani Phone",
        capabilities: Optional[List[str]] = None,
        public_key: Optional[str] = None,
    ) -> DeviceIdentity:
        """Confirm pairing from phone side using the pairing code.

        Raises:
            ValueError if session is invalid, expired, or pairing code does not match.
        """
        session = self._pending_pairing_sessions.get(session_id)
        if not session:
            raise ValueError(f"Pairing session {session_id} not found.")

        if time.time() > session["expires_at"]:
            del self._pending_pairing_sessions[session_id]
            raise ValueError("Pairing session expired. Please generate a new code.")

        if session["pairing_code"] != challenge_code.strip():
            raise ValueError("Invalid pairing code provided.")

        # Pairing approved! Generate secure token
        del self._pending_pairing_sessions[session_id]
        auth_token = generate_device_token(device_id)

        device = DeviceIdentity(
            device_id=device_id,
            device_name=device_name or session["device_name"],
            capabilities=capabilities or [
                "launch_app",
                "close_app",
                "screenshot",
                "accessibility",
                "gestures",
                "photos",
                "notifications",
                "clipboard",
            ],
            pairing_state="paired",
            connection_status="connected",
            last_seen=time.time(),
            auth_token=auth_token,
            public_key=public_key,
        )

        self.devices[device_id] = device
        if self.active_device_id is None:
            self.active_device_id = device_id

        logger.info(f"Successfully paired device {device_id} ({device.device_name})")
        return device

    def register_paired_device(self, device: DeviceIdentity) -> None:
        """Directly register an already authenticated device (e.g. from local vault)."""
        self.devices[device.device_id] = device
        if self.active_device_id is None:
            self.active_device_id = device.device_id

    def list_devices(self) -> List[DeviceIdentity]:
        """List all known paired devices with their live connection status."""
        now = time.time()
        for dev in self.devices.values():
            if dev.connection_status == "connected" and (now - dev.last_seen > self.heartbeat_timeout_sec):
                dev.connection_status = "offline"
        return list(self.devices.values())

    def get_device(self, device_id: Optional[str] = None) -> Optional[DeviceIdentity]:
        """Get device identity by ID, or return active device."""
        target_id = device_id or self.active_device_id
        if not target_id:
            return None
        dev = self.devices.get(target_id)
        if dev and dev.connection_status == "connected" and (time.time() - dev.last_seen > self.heartbeat_timeout_sec):
            dev.connection_status = "offline"
        return dev

    def set_active_device(self, device_id: str) -> bool:
        """Switch active targeted device (e.g. between Phone and Tablet)."""
        if device_id in self.devices:
            self.active_device_id = device_id
            return True
        return False

    # -------------------------------------------------------------------------
    # Connection Lifecycle
    # -------------------------------------------------------------------------

    def connect(self, device_id: Optional[str] = None) -> bool:
        """Establish or refresh connection with device."""
        dev = self.get_device(device_id)
        if not dev:
            return False
        if dev.pairing_state != "paired":
            return False
        dev.connection_status = "connected"
        dev.last_seen = time.time()
        logger.info(f"Connected to device {dev.device_id}")
        return True

    def disconnect(self, device_id: Optional[str] = None) -> bool:
        """Sever connection with device."""
        dev = self.get_device(device_id)
        if not dev:
            return False
        dev.connection_status = "disconnected"
        logger.info(f"Disconnected from device {dev.device_id}")
        return True

    def heartbeat(self, device_id: Optional[str] = None) -> bool:
        """Ping-pong keepalive signal. Updates last_seen timestamp and revives connection."""
        target_id = device_id or self.active_device_id
        if not target_id:
            return False
        dev = self.devices.get(target_id)
        if not dev or dev.connection_status == "disconnected":
            return False
        dev.connection_status = "connected"
        dev.last_seen = time.time()
        return True

    def is_connected(self, device_id: Optional[str] = None) -> bool:
        """Check if target device is currently connected and responsive."""
        dev = self.get_device(device_id)
        if not dev:
            return False
        return dev.connection_status == "connected" and (time.time() - dev.last_seen <= self.heartbeat_timeout_sec)

    # -------------------------------------------------------------------------
    # Command Dispatch & Emergency Stop
    # -------------------------------------------------------------------------

    def send_command(self, command: CommandRequest) -> CommandResponse:
        """Send a structured command to the device and await correlated response.

        Enforces:
        - Device trust check
        - Connection check (rejects if DEVICE_DISCONNECTED)
        - Transport dispatch
        - Execution timing
        """
        dev = self.get_device(command.device_id)
        if not dev:
            return CommandResponse(
                request_id=command.request_id,
                device_id=command.device_id,
                success=False,
                error=f"Device '{command.device_id}' is not paired with SHIVANI.",
            )

        if not self.is_connected(command.device_id):
            return CommandResponse(
                request_id=command.request_id,
                device_id=command.device_id,
                success=False,
                error=f"DEVICE_DISCONNECTED: Phone '{dev.device_name}' connection lost or offline.",
            )

        # Update last_seen
        dev.last_seen = time.time()

        if self._transport_handler is None:
            return CommandResponse(
                request_id=command.request_id,
                device_id=command.device_id,
                success=False,
                error="Device bridge transport handler is not configured.",
            )

        start_time = time.time()
        try:
            response = self._transport_handler(command)
            response.execution_time_ms = round((time.time() - start_time) * 1000, 2)
            return response
        except Exception as e:
            logger.error(f"Error executing command {command.action} on device {command.device_id}: {e}")
            return CommandResponse(
                request_id=command.request_id,
                device_id=command.device_id,
                success=False,
                error=str(e),
                execution_time_ms=round((time.time() - start_time) * 1000, 2),
            )

    def cancel_current_task(self, device_id: Optional[str] = None) -> CommandResponse:
        """Propagate immediate cancellation ('Shivani stop') to mobile agent."""
        target_id = device_id or self.active_device_id
        if not target_id:
            return CommandResponse(
                request_id="cancel-abort",
                device_id="unknown",
                success=False,
                error="No active device to cancel.",
            )

        cancel_cmd = CommandRequest(
            device_id=target_id,
            action="cancel_task",
            parameters={"reason": "User emergency stop command"},
        )
        logger.warning(f"Sending emergency cancellation to device {target_id}")
        return self.send_command(cancel_cmd)

    def receive_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle incoming asynchronous event from phone and notify listeners."""
        for listener in self._event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Error notifying event listener: {e}")
