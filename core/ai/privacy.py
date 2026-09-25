"""Privacy-Aware Data Classification & Cloud Context Filtering for Phase 19.

Scans inputs for credentials, API tokens, private keys, financial data, and personal documents.
Enforces local execution for SENSITIVE/CRITICAL content and redacts secrets before any cloud call.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from core.ai.models import PrivacyLevel

logger = logging.getLogger("shivani.ai.privacy")

# Regex patterns for detecting credentials and sensitive tokens
SECRET_PATTERNS = [
    re.compile(r"(?i)(?:api_key|token|bearer|secret|password|passwd|auth)[\s:=]+['\"]?([a-zA-Z0-9_\-\.]{8,})['\"]?"),
    re.compile(r"sk-[a-zA-Z0-9]{32,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),  # Credit card pattern
]

PRIVATE_KEYWORDS = [
    "salary", "payroll", "tax return", "bank account", "private key", "confidential",
    "internal only", "medical record", "ssn", "passport", "aadhaar",
]


class DataClassifier:
    """Classifies user inputs, task queries, and document contents into privacy tiers."""

    @classmethod
    def classify(cls, text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[PrivacyLevel, List[str]]:
        """Determine privacy level and list detected sensitivity indicators."""
        meta = metadata or {}
        reasons = []

        # 1. Check for explicit secrets (CRITICAL)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                reasons.append("Detected cryptographic secret, API token, or credential.")
                return PrivacyLevel.CRITICAL, reasons

        # 2. Check metadata or path hints
        file_path = meta.get("file_path", "").lower()
        if any(k in file_path for k in [".env", "id_rsa", "credentials", "secrets", "keystore"]):
            reasons.append(f"Referenced file '{file_path}' is a sensitive credential store.")
            return PrivacyLevel.CRITICAL, reasons

        # 3. Check for private financial or personal keywords (SENSITIVE)
        text_lower = text.lower()
        matched_keywords = [k for k in PRIVATE_KEYWORDS if k in text_lower]
        if matched_keywords:
            reasons.append(f"Contains sensitive terms: {', '.join(matched_keywords)}")
            return PrivacyLevel.SENSITIVE, reasons

        # 4. Check for local personal files (PRIVATE)
        if any(p in text_lower for p in ["my document", "my file", "private", "personal note", "download folder"]):
            reasons.append("Contains reference to user's local personal documents.")
            return PrivacyLevel.PRIVATE, reasons

        # 5. Low sensitivity or Public
        if any(g in text_lower for g in ["what is", "how to", "python", "explain", "who is", "weather", "search", "news"]):
            return PrivacyLevel.PUBLIC, ["General public knowledge query."]

        return PrivacyLevel.LOW_SENSITIVITY, ["Standard non-confidential query."]


class CloudContextFilter:
    """Filter that sanitizes context packets and prevents leaks before cloud transmission."""

    @classmethod
    def sanitize_for_cloud(
        cls,
        text: str,
        privacy_level: PrivacyLevel,
        allow_cloud: bool = True,
    ) -> Tuple[str, bool]:
        """Scrub sensitive credentials and ensure compliance with privacy policies.

        Returns:
            Tuple of (sanitized_text, was_redacted)
        Raises:
            PermissionError if privacy level is CRITICAL and cloud transmission is prohibited.
        """
        if privacy_level == PrivacyLevel.CRITICAL:
            raise PermissionError("Critical secret data detected. Cloud transmission is strictly blocked.")

        if not allow_cloud:
            raise PermissionError("Cloud access is disabled by user policy.")

        sanitized = text
        was_redacted = False

        # Redact any accidental tokens or keys
        for pattern in SECRET_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub(r"***REDACTED_SECRET***", sanitized)
                was_redacted = True

        return sanitized, was_redacted
