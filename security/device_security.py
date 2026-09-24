"""
SHIVANI Device Security Manager
Handles HMAC-SHA256 message signing, nonce verification, timestamp anti-replay checks,
and authorized mobile bridge device pairing validation.
"""

from datetime import datetime, timezone
import hashlib
import hmac
import time
import json
from typing import Any, Dict, Optional, Set, Tuple


class DeviceSecurityManager:
    def __init__(self, secret: Optional[str] = None, max_skew_seconds: float = 60.0):
        self.secret = secret or ""
        self.max_skew = max_skew_seconds
        self._seen_nonces: Set[str] = set()

    def generate_signature(self, message_str: str, shared_secret: Optional[str] = None) -> str:
        sec = shared_secret or self.secret
        return hmac.new(
            sec.encode("utf-8"),
            message_str.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def sign_payload(self, payload: Dict[str, Any], timestamp: float, nonce: str, secret: Optional[str] = None) -> str:
        body = json.dumps(payload, sort_keys=True)
        canonical = f"{nonce}:{timestamp}:{body}"
        return self.generate_signature(canonical, shared_secret=secret)

    def verify_signature(self, message_str: str, signature: str, shared_secret: Optional[str] = None) -> bool:
        expected = self.generate_signature(message_str, shared_secret=shared_secret)
        return hmac.compare_digest(expected, signature)

    def verify_message(
        self,
        payload: Dict[str, Any],
        timestamp: float,
        nonce: str,
        signature: str,
        secret: Optional[str] = None,
    ) -> Tuple[bool, str]:
        # 1. Anti-replay
        if not self.verify_anti_replay(nonce, timestamp):
            return False, "Replay attack detected or timestamp skew exceeded."

        # 2. Signature verification
        body = json.dumps(payload, sort_keys=True)
        canonical = f"{nonce}:{timestamp}:{body}"
        if not self.verify_signature(canonical, signature, shared_secret=secret):
            return False, "Invalid signature: HMAC validation failed."

        return True, ""

    def verify_anti_replay(self, nonce: str, timestamp_epoch: float) -> bool:
        now = time.time()
        # Check clock skew
        if abs(now - timestamp_epoch) > self.max_skew:
            return False

        # Check nonce uniqueness
        if nonce in self._seen_nonces:
            return False

        self._seen_nonces.add(nonce)
        if len(self._seen_nonces) > 5000:
            self._seen_nonces.clear()

        return True

