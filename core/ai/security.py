"""Model Security Boundary & Prompt Injection Defense for Phase 19.

Enforces the core rule:
A model is an untrusted reasoning component, NOT an execution authority.
All model outputs must undergo structured parsing, permission checks, and tool validation.
Never: MODEL OUTPUT -> shell.execute() without validation.
"""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from security.permissions.engine import RiskLevel

logger = logging.getLogger("shivani.ai.security")

# Common prompt injection patterns in external content (webpages, emails, PDFs)
INJECTION_PATTERNS = [
    re.compile(r"(?i)ignore\s+(?:all\s+)?previous\s+instructions"),
    re.compile(r"(?i)disregard\s+(?:all\s+)?prior\s+commands"),
    re.compile(r"(?i)you\s+are\s+now\s+in\s+developer\s+mode"),
    re.compile(r"(?i)system\s+override:\s*disable\s+permissions"),
    re.compile(r"(?i)elevate\s+privileges\s+to\s+root"),
]


class ModelSecurityBoundary:
    """Validates model outputs, sanitizes untrusted tool arguments, and defends against injection."""

    @classmethod
    def sanitize_external_context(cls, text: str) -> Tuple[str, bool]:
        """Strip known adversarial jailbreaks from ingested external content before prompt injection."""
        sanitized = text
        detected = False
        for pattern in INJECTION_PATTERNS:
            if pattern.search(sanitized):
                sanitized = pattern.sub(r"[INJECTION_ATTEMPT_FILTERED]", sanitized)
                detected = True

        if detected:
            logger.warning("Filtered prompt injection attempt from ingested external document.")
        return sanitized, detected

    @classmethod
    def validate_action_proposal(
        cls,
        tool_name: str,
        arguments: Dict[str, Any],
        user_permission_tier: str = "SAFE",
    ) -> Tuple[bool, Optional[str]]:
        """Strict validation of a proposed tool execution.

        Models cannot grant themselves permission to execute destructive tools.
        """
        # Block arbitrary command execution injection
        if tool_name in ("terminal.execute", "terminal_exec"):
            cmd = arguments.get("command", "").lower().strip()
            # Hardcoded blocked destructive commands
            if any(b in cmd for b in ["rm -rf", "format ", "del /f /s /q c:", "drop database"]):
                return False, f"Destructive command '{cmd}' blocked by security boundary."

        return True, None
