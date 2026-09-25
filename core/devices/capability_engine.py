"""Capability Discovery, Negotiation & Permission Enforcement Engine for Phase 18.

Verifies hardware/software capabilities, negotiates device feature sets, and enforces
strict permission boundaries (VIEW, COMMAND, CONTROL, TRANSFER, ADMIN) with anti-replay protection.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from core.devices.models import (
    CrossDeviceCommand,
    Device,
    DeviceCapability,
    DevicePermission,
    DeviceTrustState,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.capability")

# Map of standard actions to their required capability and minimum permission tier
ACTION_REQUIREMENTS: Dict[str, Tuple[Optional[DeviceCapability], DevicePermission]] = {
    # Read-only / status actions
    "get_status": (None, DevicePermission.VIEW),
    "get_battery": (None, DevicePermission.VIEW),
    "list_files": (DeviceCapability.FILES, DevicePermission.VIEW),
    "get_notifications": (DeviceCapability.NOTIFICATIONS, DevicePermission.VIEW),
    "read_clipboard": (DeviceCapability.CLIPBOARD, DevicePermission.VIEW),
    
    # Command actions
    "launch_app": (DeviceCapability.UI_AUTOMATION, DevicePermission.COMMAND),
    "close_app": (DeviceCapability.UI_AUTOMATION, DevicePermission.COMMAND),
    "send_notification": (DeviceCapability.NOTIFICATIONS, DevicePermission.COMMAND),
    "handoff_task": (None, DevicePermission.COMMAND),
    
    # File & clipboard transfer actions
    "transfer_file": (DeviceCapability.FILES, DevicePermission.TRANSFER),
    "write_clipboard": (DeviceCapability.CLIPBOARD, DevicePermission.TRANSFER),
    
    # Deep control actions
    "tap_coordinate": (DeviceCapability.UI_AUTOMATION, DevicePermission.CONTROL),
    "swipe": (DeviceCapability.UI_AUTOMATION, DevicePermission.CONTROL),
    "press_key": (DeviceCapability.UI_AUTOMATION, DevicePermission.CONTROL),
    "desktop_click": (DeviceCapability.COMPUTER_CONTROL, DevicePermission.CONTROL),
    "terminal_exec": (DeviceCapability.TERMINAL, DevicePermission.CONTROL),
    "camera_capture": (DeviceCapability.CAMERA, DevicePermission.CONTROL),
    
    # Administrative & emergency actions
    "pair_device": (None, DevicePermission.ADMIN),
    "revoke_device": (None, DevicePermission.ADMIN),
    "update_permissions": (None, DevicePermission.ADMIN),
    "emergency_stop": (None, DevicePermission.ADMIN),
}

# Permission hierarchy rank (higher numbers encompass lower permissions)
PERMISSION_HIERARCHY: Dict[str, int] = {
    DevicePermission.VIEW.value: 1,
    DevicePermission.COMMAND.value: 2,
    DevicePermission.TRANSFER.value: 3,
    DevicePermission.CONTROL.value: 4,
    DevicePermission.ADMIN.value: 5,
}


class CapabilityEngine:
    """Discovers, validates, and enforces capabilities and permissions for cross-device operations."""

    def __init__(self, trust_store: TrustStore, max_timestamp_skew_sec: float = 60.0):
        self.trust_store = trust_store
        self.max_timestamp_skew_sec = max_timestamp_skew_sec
        self._seen_nonces: Set[str] = set()

    def discover_capabilities(self, device: Device) -> List[str]:
        """Return the registered capability list for a device."""
        return list(device.capabilities)

    def negotiate_capabilities(self, device_a: Device, device_b: Device) -> Set[str]:
        """Find common intersection of capabilities between two devices (for mutual handoffs)."""
        caps_a = set(device_a.capabilities)
        caps_b = set(device_b.capabilities)
        return caps_a.intersection(caps_b)

    def check_permission(self, device: Device, required_permission: DevicePermission | str) -> bool:
        """Check if device permissions meet or exceed the required permission tier."""
        req_perm = required_permission.value if isinstance(required_permission, DevicePermission) else required_permission
        
        # Admin permission always satisfies any check
        if DevicePermission.ADMIN.value in device.permissions:
            return True

        req_rank = PERMISSION_HIERARCHY.get(req_perm, 99)
        for perm in device.permissions:
            perm_val = perm.value if isinstance(perm, DevicePermission) else perm
            if PERMISSION_HIERARCHY.get(perm_val, 0) >= req_rank:
                return True
        return False

    def validate_command(self, cmd: CrossDeviceCommand) -> Tuple[bool, Optional[str]]:
        """Validate an incoming cross-device command against trust, replay protection, capability, and permission."""
        # 1. Anti-replay verification (timestamp skew)
        now = time.time()
        if abs(now - cmd.timestamp) > self.max_timestamp_skew_sec:
            msg = f"Command timestamp skewed by {abs(now - cmd.timestamp):.1f}s (max allowed: {self.max_timestamp_skew_sec}s)."
            logger.warning(msg)
            return False, msg

        # 2. Anti-replay verification (nonce reuse)
        if cmd.nonce in self._seen_nonces:
            msg = f"Replay attack detected: Nonce '{cmd.nonce}' has already been processed."
            logger.warning(msg)
            return False, msg
        self._seen_nonces.add(cmd.nonce)
        # Limit nonce cache size
        if len(self._seen_nonces) > 10000:
            self._seen_nonces.clear()

        # 3. Source device trust verification
        source_dev = self.trust_store.get_device(cmd.source_device_id)
        if not source_dev:
            return False, f"Source device '{cmd.source_device_id}' is unknown."

        if source_dev.trust_state != DeviceTrustState.TRUSTED:
            return False, f"Source device '{cmd.source_device_id}' is not TRUSTED (state: {source_dev.trust_state.value})."

        # 4. Target device existence and reachability
        target_dev = self.trust_store.get_device(cmd.target_device_id)
        if not target_dev:
            return False, f"Target device '{cmd.target_device_id}' is unknown."

        # 5. Check action requirements
        req = ACTION_REQUIREMENTS.get(cmd.action)
        if req:
            req_cap, req_perm = req
            
            # Target must have capability if required
            if req_cap and not target_dev.has_capability(req_cap):
                return False, f"Target device '{target_dev.display_name}' lacks required capability '{req_cap.value}'."

            # Source must have adequate permission
            if not self.check_permission(source_dev, req_perm):
                return False, f"Source device '{source_dev.display_name}' lacks required permission '{req_perm.value}' for action '{cmd.action}'."

        return True, None
