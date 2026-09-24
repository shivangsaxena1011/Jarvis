"""Cryptographic helper functions for Device Bridge pairing and authentication.

Implements pairing code generation, HMAC-SHA256 signature verification, and token exchange.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Tuple


def generate_pairing_code() -> str:
    """Generate a high-entropy 6-digit numeric pairing challenge code."""
    # Uses secrets module for cryptographically secure random number generation
    return f"{secrets.randbelow(900000) + 100000}"


def generate_device_token(device_id: str) -> str:
    """Generate a cryptographically secure random session auth token."""
    raw = secrets.token_bytes(32)
    salt = device_id.encode("utf-8")
    return hashlib.sha256(raw + salt).hexdigest()


def sign_payload(payload: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 signature for a payload."""
    return hmac.new(
        secret_key.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()


def verify_signature(payload: str, secret_key: str, expected_signature: str) -> bool:
    """Safely verify HMAC-SHA256 signature using constant-time comparison."""
    actual_sig = sign_payload(payload, secret_key)
    return hmac.compare_digest(actual_sig, expected_signature)
