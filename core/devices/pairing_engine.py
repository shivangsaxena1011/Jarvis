"""Pairing & Cryptographic Trust Engine for Phase 18.

Implements secure out-of-band mutual authentication, 6-digit Short Authentication String (SAS)
challenge-response, session expiration, token issuance, and device trust lifecycle management.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from core.devices.models import (
    Device,
    DeviceCapability,
    DevicePermission,
    DeviceTrustState,
    PairingSession,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.pairing")

# Visual Short Authentication String (SAS) wordlist for out-of-band human verification
SAS_WORDS = [
    "amber", "blaze", "comet", "delta", "echo", "frost", "galaxy", "harbor",
    "indigo", "jupiter", "kestrel", "lunar", "meteor", "nebula", "orion", "phoenix",
    "pulsar", "quantum", "radar", "solaris", "titan", "umbra", "vortex", "zenith",
]


class PairingEngine:
    """Manages secure device onboarding, mutual SAS verification, and trust transitions."""

    def __init__(self, trust_store: TrustStore, code_ttl_sec: float = 300.0):
        self.trust_store = trust_store
        self.code_ttl_sec = code_ttl_sec

    def generate_sas_code(self) -> Tuple[str, str]:
        """Generate a cryptographically random 6-digit code and a corresponding SAS word phrase."""
        num = secrets.randbelow(1000000)
        code = f"{num:06d}"
        w1 = SAS_WORDS[num % len(SAS_WORDS)]
        w2 = SAS_WORDS[(num // len(SAS_WORDS)) % len(SAS_WORDS)]
        phrase = f"{w1}-{w2}"
        return code, phrase

    def initiate_pairing(
        self,
        device_id: str,
        display_name: str,
        platform: str,
        public_key: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[str, str, str]:
        """Initiate an onboarding session for a new or reconnecting device.

        Returns:
            Tuple of (session_id, 6_digit_code, sas_phrase)
        """
        existing = self.trust_store.get_device(device_id)
        if existing and existing.trust_state == DeviceTrustState.BLOCKED:
            raise PermissionError(f"Device {device_id} is BLOCKED and cannot pair.")

        code, sas_phrase = self.generate_sas_code()
        session_id = f"pair-{uuid.uuid4().hex[:12]}"
        
        session = PairingSession(
            session_id=session_id,
            device_id=device_id,
            display_name=display_name,
            platform=platform,
            code=code,
            public_key=public_key,
            created_at=time.time(),
            expires_at=time.time() + self.code_ttl_sec,
            metadata={"sas_phrase": sas_phrase, **(metadata or {})},
        )
        self.trust_store.save_pairing_session(session)

        # Record initial device in DISCOVERED / PAIRING state
        dev = Device(
            device_id=device_id,
            display_name=display_name,
            platform=platform,
            trust_state=DeviceTrustState.PAIRING,
            public_key=public_key,
            last_seen=time.time(),
            metadata=metadata or {},
        )
        self.trust_store.upsert_device(dev)

        logger.info(f"Initiated pairing for {device_id} ('{display_name}') [Session: {session_id}, Code: {code}]")
        return session_id, code, sas_phrase

    def confirm_pairing(
        self,
        session_id: str,
        code_attempt: str,
        capabilities: Optional[List[str]] = None,
        public_key: Optional[str] = None,
        ip_address: Optional[str] = None,
        port: int = 8765,
    ) -> Device:
        """Verify the 6-digit confirmation code and transition device to TRUSTED."""
        session = self.trust_store.get_pairing_session(session_id)
        if not session:
            raise ValueError(f"Pairing session '{session_id}' not found or already completed.")

        if session.is_expired():
            self.trust_store.delete_pairing_session(session_id)
            raise TimeoutError("Pairing session has expired. Please initiate a new pairing request.")

        # Constant-time comparison to prevent timing side-channels
        if not hmac.compare_digest(session.code.strip(), code_attempt.strip()):
            logger.warning(f"Invalid pairing code attempt for session {session_id}")
            raise ValueError("Invalid pairing code provided.")

        # Pairing successful: generate device auth token
        auth_token = f"shv-tok-{secrets.token_urlsafe(32)}"
        final_public_key = public_key or session.public_key

        # Standard default capabilities based on platform
        default_caps = capabilities or [
            DeviceCapability.NOTIFICATIONS.value,
            DeviceCapability.FILES.value,
            DeviceCapability.CLIPBOARD.value,
        ]

        # Initial default permissions for newly paired device: VIEW, COMMAND, TRANSFER
        default_perms = [
            DevicePermission.VIEW.value,
            DevicePermission.COMMAND.value,
            DevicePermission.TRANSFER.value,
        ]

        device = Device(
            device_id=session.device_id,
            display_name=session.display_name,
            platform=session.platform,
            capabilities=default_caps,
            trust_state=DeviceTrustState.TRUSTED,
            permissions=default_perms,
            public_key=final_public_key,
            auth_token=auth_token,
            ip_address=ip_address,
            port=port,
            last_seen=time.time(),
            metadata=session.metadata,
        )
        self.trust_store.upsert_device(device)
        self.trust_store.delete_pairing_session(session_id)

        logger.info(f"Successfully paired device {device.device_id} ({device.display_name}) with TRUSTED status.")
        return device

    def revoke_device(self, device_id: str) -> bool:
        """Immediately revoke trust and invalidate authentication for a device."""
        device = self.trust_store.get_device(device_id)
        if not device:
            return False
        device.trust_state = DeviceTrustState.REVOKED
        device.auth_token = None
        self.trust_store.upsert_device(device)
        logger.warning(f"Revoked device trust for {device_id}")
        return True

    def block_device(self, device_id: str) -> bool:
        """Block a device from connecting or initiating pairing."""
        device = self.trust_store.get_device(device_id)
        if not device:
            device = Device(
                device_id=device_id,
                display_name="Blocked Device",
                trust_state=DeviceTrustState.BLOCKED,
            )
        else:
            device.trust_state = DeviceTrustState.BLOCKED
            device.auth_token = None
        self.trust_store.upsert_device(device)
        logger.warning(f"Blocked device {device_id}")
        return True

    def unblock_device(self, device_id: str) -> bool:
        """Unblock a previously blocked device, resetting it to DISCOVERED."""
        device = self.trust_store.get_device(device_id)
        if not device:
            return False
        device.trust_state = DeviceTrustState.DISCOVERED
        self.trust_store.upsert_device(device)
        logger.info(f"Unblocked device {device_id}")
        return True

    def verify_auth_token(self, device_id: str, auth_token: str) -> bool:
        """Validate if an incoming request contains a valid token for an active TRUSTED device."""
        device = self.trust_store.get_device(device_id)
        if not device or device.trust_state != DeviceTrustState.TRUSTED:
            return False
        if not device.auth_token:
            return False
        return hmac.compare_digest(device.auth_token, auth_token)
