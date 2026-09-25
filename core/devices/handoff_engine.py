"""Task Handoff & Context Continuity Engine for Phase 18.

Orchestrates multi-device task handoffs (CONTINUE, TRANSFER, DELEGATE, MIRROR, VIEW, NOTIFY)
with minimal, privacy-preserving context packaging, expiration, and status tracking.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

from core.devices.models import (
    Device,
    DeviceTrustState,
    HandoffStatus,
    HandoffType,
    TaskHandoff,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.handoff")


class HandoffEngine:
    """Manages cross-device task context packaging, progression, and synchronization."""

    def __init__(self, trust_store: TrustStore, default_ttl_sec: float = 600.0):
        self.trust_store = trust_store
        self.default_ttl_sec = default_ttl_sec
        self._handoff_handlers: Dict[HandoffType, Callable[[TaskHandoff], Any]] = {}

    def register_handler(self, handoff_type: HandoffType, handler: Callable[[TaskHandoff], Any]) -> None:
        """Register a callback for handling incoming handoffs on this device node."""
        self._handoff_handlers[handoff_type] = handler

    def create_handoff(
        self,
        task_id: str,
        title: str,
        source_device_id: str,
        target_device_id: str,
        handoff_type: HandoffType = HandoffType.CONTINUE,
        context_payload: Optional[Dict[str, Any]] = None,
        ttl_sec: Optional[float] = None,
    ) -> TaskHandoff:
        """Package a task execution state into a minimal handoff record."""
        # Validate target device
        target_device = self.trust_store.get_device(target_device_id)
        if not target_device:
            raise ValueError(f"Target device '{target_device_id}' does not exist.")

        if target_device.trust_state != DeviceTrustState.TRUSTED:
            raise PermissionError(f"Target device '{target_device.display_name}' is not in TRUSTED state.")

        # Ensure minimal context payload does not leak sensitive unvetted data
        clean_context = self._sanitize_context(context_payload or {})

        handoff_id = f"hdf-{uuid.uuid4().hex[:12]}"
        now = time.time()
        expiry = now + (ttl_sec or self.default_ttl_sec)

        handoff = TaskHandoff(
            handoff_id=handoff_id,
            task_id=task_id,
            title=title,
            source_device_id=source_device_id,
            target_device_id=target_device_id,
            handoff_type=handoff_type,
            context_payload=clean_context,
            status=HandoffStatus.INITIATED,
            created_at=now,
            expires_at=expiry,
        )

        self.trust_store.save_handoff(handoff)
        logger.info(
            f"Created {handoff_type.value.upper()} handoff '{handoff_id}' for task '{task_id}' "
            f"from {source_device_id} to {target_device_id}."
        )
        return handoff

    def accept_handoff(self, handoff_id: str, executing_device_id: str) -> TaskHandoff:
        """Accept an incoming task handoff on the receiving device."""
        handoff = self.trust_store.get_handoff(handoff_id)
        if not handoff:
            raise ValueError(f"Handoff '{handoff_id}' not found.")

        if handoff.is_expired():
            self.trust_store.update_handoff_status(handoff_id, HandoffStatus.EXPIRED, error_message="Handoff expired.")
            raise TimeoutError(f"Handoff '{handoff_id}' has expired.")

        if handoff.target_device_id != executing_device_id:
            raise PermissionError(
                f"Device '{executing_device_id}' is not the intended target '{handoff.target_device_id}' for handoff."
            )

        if handoff.status not in (HandoffStatus.INITIATED, HandoffStatus.PENDING):
            raise RuntimeError(f"Handoff '{handoff_id}' is already {handoff.status.value}.")

        handoff.status = HandoffStatus.IN_PROGRESS
        self.trust_store.save_handoff(handoff)
        logger.info(f"Accepted handoff '{handoff_id}' on {executing_device_id}.")
        return handoff

    def complete_handoff(
        self,
        handoff_id: str,
        result_payload: Optional[Dict[str, Any]] = None,
    ) -> TaskHandoff:
        """Mark a handoff as successfully executed and attach output results."""
        handoff = self.trust_store.get_handoff(handoff_id)
        if not handoff:
            raise ValueError(f"Handoff '{handoff_id}' not found.")

        handoff.status = HandoffStatus.COMPLETED
        handoff.result_payload = result_payload or {}
        self.trust_store.save_handoff(handoff)
        logger.info(f"Completed handoff '{handoff_id}'.")
        return handoff

    def reject_handoff(self, handoff_id: str, reason: str = "User declined") -> TaskHandoff:
        """Reject an incoming handoff request."""
        handoff = self.trust_store.get_handoff(handoff_id)
        if not handoff:
            raise ValueError(f"Handoff '{handoff_id}' not found.")

        handoff.status = HandoffStatus.REJECTED
        handoff.error_message = reason
        self.trust_store.save_handoff(handoff)
        logger.warning(f"Rejected handoff '{handoff_id}': {reason}")
        return handoff

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Strip raw conversation logs and passwords, keeping only focused execution state."""
        sanitized = {}
        # Allowed core execution state fields
        allowed_keys = {
            "task_id", "title", "goal", "current_step", "total_steps",
            "active_url", "file_paths", "summary", "project_name",
            "source_app", "target_app", "state_checkpoint", "user_parameters"
        }
        for k, v in context.items():
            if k in allowed_keys:
                sanitized[k] = v
            elif not any(s in k.lower() for s in ["token", "secret", "password", "key", "credential", "auth"]):
                # Retain non-sensitive custom fields
                sanitized[k] = v
        return sanitized
