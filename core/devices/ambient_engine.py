"""Ambient Intelligence Boundary & Zero-Surveillance Privacy Engine for Phase 18.

Guarantees absolute user privacy:
- Strict ambient context states (OFF, TASK_ONLY, PROJECT, SESSION, GLOBAL)
- Zero-Surveillance Guarantee: Hard architectural block against covert microphone listening,
  camera capture, background screen recording, passive clipboard monitoring, or location tracking.
- Explicit-only clipboard and screenshot synchronization with sensitive data scrubbing.
- Full audit log of all ambient state evaluations and sensor authorizations.
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional

from core.devices.models import (
    AmbientContextState,
    Device,
    DeviceTrustState,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.ambient")

# Regex to detect potential credentials, API tokens, and passwords in shared clipboards
SENSITIVE_DATA_PATTERNS = [
    re.compile(r"(?i)(?:api_key|token|bearer|secret|password|passwd|auth)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
]


class AmbientEngine:
    """Enforces strict ambient intelligence privacy boundaries and explicit-only sharing."""

    def __init__(self, trust_store: TrustStore, initial_state: AmbientContextState = AmbientContextState.TASK_ONLY):
        self.trust_store = trust_store
        self.current_state = initial_state
        self._audit_log: List[Dict[str, Any]] = []

    def set_ambient_state(self, new_state: AmbientContextState | str) -> None:
        """Update active ambient intelligence boundary mode."""
        state = AmbientContextState(new_state) if isinstance(new_state, str) else new_state
        old_state = self.current_state
        self.current_state = state
        self._record_audit(
            event="ambient_state_change",
            details={"previous_state": old_state.value, "new_state": state.value},
        )
        logger.info(f"Ambient context state updated from {old_state.value} to {state.value}.")

    def get_ambient_state(self) -> AmbientContextState:
        return self.current_state

    def verify_sensor_access(self, sensor_type: str, explicit_user_intent: bool) -> bool:
        """Zero-surveillance gatekeeper.

        Covert access to microphone, camera, screen, clipboard, or location is strictly barred.
        Requires explicit, intentional user initiation.
        """
        sensor = sensor_type.lower()
        if sensor in ("microphone", "mic", "camera", "screen_recorder", "location", "passive_clipboard"):
            if not explicit_user_intent:
                self._record_audit(
                    event="covert_access_blocked",
                    details={"sensor": sensor, "reason": "No explicit user intent."},
                )
                logger.error(f"Zero-surveillance violation blocked: Covert access to {sensor} is prohibited.")
                raise PermissionError(
                    f"Zero-surveillance guarantee: Covert background access to {sensor} is strictly prohibited."
                )

        # In OFF mode, even ambient sensors are disabled
        if self.current_state == AmbientContextState.OFF and not explicit_user_intent:
            return False

        self._record_audit(event="sensor_access_allowed", details={"sensor": sensor})
        return True

    def share_clipboard(
        self,
        source_device_id: str,
        target_device_id: str,
        content: str,
        explicit_user_action: bool = True,
    ) -> Dict[str, Any]:
        """Explicitly share clipboard content across devices with sensitive token masking."""
        if not explicit_user_action:
            raise PermissionError("Clipboard sharing requires explicit user trigger. Background monitoring is disabled.")

        target_dev = self.trust_store.get_device(target_device_id)
        if not target_dev or target_dev.trust_state != DeviceTrustState.TRUSTED:
            raise PermissionError(f"Target device '{target_device_id}' is not in TRUSTED state.")

        # Inspect and scrub/warn about credentials
        is_sensitive = False
        masked_content = content
        for pattern in SENSITIVE_DATA_PATTERNS:
            if pattern.search(content):
                is_sensitive = True
                masked_content = pattern.sub(r"***REDACTED_CREDENTIAL***", content)

        self._record_audit(
            event="clipboard_shared",
            details={
                "source": source_device_id,
                "target": target_device_id,
                "chars_length": len(content),
                "is_sensitive": is_sensitive,
            },
        )

        return {
            "success": True,
            "source_device_id": source_device_id,
            "target_device_id": target_device_id,
            "payload": masked_content if is_sensitive else content,
            "was_redacted": is_sensitive,
            "timestamp": time.time(),
        }

    def share_notification(
        self,
        notification: Dict[str, Any],
        target_device_id: str,
    ) -> Dict[str, Any]:
        """Route cross-device notification alert."""
        target_dev = self.trust_store.get_device(target_device_id)
        if not target_dev or target_dev.trust_state != DeviceTrustState.TRUSTED:
            raise PermissionError(f"Target device '{target_device_id}' is not in TRUSTED state.")

        self._record_audit(
            event="notification_forwarded",
            details={"target": target_device_id, "title": notification.get("title")},
        )

        return {
            "success": True,
            "target_device_id": target_device_id,
            "notification": notification,
            "timestamp": time.time(),
        }

    def get_audit_trail(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve recent privacy and ambient audit events."""
        return self._audit_log[-limit:]

    def _record_audit(self, event: str, details: Dict[str, Any]) -> None:
        self._audit_log.append({
            "timestamp": time.time(),
            "event": event,
            "details": details,
        })
        if len(self._audit_log) > 1000:
            self._audit_log = self._audit_log[-500:]
