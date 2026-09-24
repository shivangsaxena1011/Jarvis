"""
SHIVANI Automation Permissions & Security Guardrails (Phase 15).
Scoped privilege boundaries, high-risk approval gating, and prompt-injection defense.
"""

from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

from core.automation.models import Automation, AutomationPermissions, AutomationStep
from security.permissions.engine import PermissionEngine
from security.permissions.models import RiskLevel, ApprovalRequest, ApprovalStatus


class SecurityBoundaryViolation(Exception):
    """Raised when an automation attempts an action outside its declared boundaries."""
    pass


class AutomationPermissionEvaluator:
    """Evaluates whether an automation action adheres to its declared security boundaries."""

    def __init__(self, permission_engine: PermissionEngine):
        self.permission_engine = permission_engine

    def evaluate_step(
        self,
        automation: Automation,
        step: AutomationStep,
        target_path: Optional[str] = None,
        target_device: Optional[str] = None,
        target_account: Optional[str] = None,
    ) -> Tuple[bool, bool, str]:
        """
        Evaluates permissions for an automation step.
        Returns:
            Tuple of (is_allowed: bool, requires_approval: bool, reason: str)
        """
        perms = automation.permissions
        step_risk = step.risk_level

        # 1. Capability Check
        if perms.allowed_capabilities and "*" not in perms.allowed_capabilities:
            tool_cap = step.tool.split(".")[0] if step.tool and "." in step.tool else (step.tool or "")
            action_cap = step.action.split(".")[0] if step.action and "." in step.action else (step.action or "")
            caps = {tool_cap, action_cap, step.tool, step.action}
            if "gmail" in caps:
                caps.add("email")
            if "email" in caps:
                caps.add("gmail")
            if "notify_user" in caps or "notify" in caps:
                caps.add("notifications")
            if "summary" in caps or "synthesize" in caps:
                caps.add("content")
                caps.add("knowledge")

            if not any(c in perms.allowed_capabilities for c in caps if c):
                return False, False, f"Capability '{tool_cap or action_cap}' is not permitted for automation '{automation.name}'"

        # 2. File Path Scope Check
        if target_path and perms.allowed_file_paths:
            normalized_target = str(Path(target_path).resolve()).replace("\\", "/")
            allowed = False
            for p in perms.allowed_file_paths:
                norm_p = str(Path(p).resolve()).replace("\\", "/")
                if normalized_target.startswith(norm_p):
                    allowed = True
                    break
            if not allowed:
                return False, False, f"File path '{target_path}' is outside permitted paths: {perms.allowed_file_paths}"

        # 3. Device Scope Check
        if target_device and perms.allowed_devices:
            if target_device not in perms.allowed_devices and "*" not in perms.allowed_devices:
                return False, False, f"Device '{target_device}' is not in allowed devices: {perms.allowed_devices}"

        # 4. Account Scope Check
        if target_account and perms.allowed_accounts:
            if target_account not in perms.allowed_accounts and "*" not in perms.allowed_accounts:
                return False, False, f"Account '{target_account}' is not permitted: {perms.allowed_accounts}"

        # 5. Pre-approved Tools
        if step.tool in perms.preapproved_tools:
            return True, False, "Pre-approved within automation scope"

        # 6. Risk Level & Approval Evaluation
        # If step risk exceeds declared max risk level -> requires human approval
        if self._risk_rank(step_risk) > self._risk_rank(perms.max_risk_level):
            return True, True, f"Step risk ({step_risk.value}) exceeds max declared risk ({perms.max_risk_level.value})"

        # Mandatory human approval for high-risk / critical operations
        if step_risk in (RiskLevel.HIGH_RISK, RiskLevel.CRITICAL) or step.requires_approval:
            return True, True, f"High-risk action ({step.action}) requires explicit confirmation"

        # System PermissionEngine policy check
        if self.permission_engine.requires_approval(step_risk):
            return True, True, f"System security policy ({self.permission_engine.policy}) requires approval"

        return True, False, "Allowed"

    @staticmethod
    def _risk_rank(risk: RiskLevel) -> int:
        ranks = {
            RiskLevel.SAFE: 0,
            RiskLevel.LOW_RISK: 1,
            RiskLevel.SENSITIVE: 2,
            RiskLevel.HIGH_RISK: 3,
            RiskLevel.CRITICAL: 4,
        }
        return ranks.get(risk, 2)


# ==============================================================================
# PROMPT INJECTION DEFENSE
# ==============================================================================

class PromptInjectionDefense:
    """
    Sanitizes untrusted external input (emails, web scraping, git commit messages,
    device notifications) and ensures external content is treated as DATA, not AUTHORITY.
    """

    INJECTION_PATTERNS = [
        r"(?i)ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"(?i)disregard\s+(all\s+)?(previous|prior)\s+instructions",
        r"(?i)you\s+are\s+now\s+in\s+developer\s+mode",
        r"(?i)new\s+system\s+prompt\s*:",
        r"(?i)send\s+(all\s+)?(files|passwords|credentials|keys)\s+to",
        r"(?i)delete\s+(all\s+)?files",
        r"(?i)format\s+drive",
        r"(?i)curl\s+.*\s*\|\s*(ba)?sh",
        r"(?i)powershell\s+-enc",
        r"(?i)override\s+(all\s+)?permissions",
    ]

    @classmethod
    def sanitize_untrusted_text(cls, text: str) -> str:
        """Wraps external content in explicit data encapsulation boundaries."""
        if not text:
            return ""
        # Strip potential template or instruction injection markers
        cleaned = text.replace("```system", "```data").replace("```assistant", "```data")
        return f"<UNTRUSTED_EXTERNAL_DATA>\n{cleaned}\n</UNTRUSTED_EXTERNAL_DATA>"

    @classmethod
    def detect_injection_attempt(cls, text: str) -> Tuple[bool, Optional[str]]:
        """Returns True and the matched pattern if a prompt injection pattern is detected."""
        if not text:
            return False, None
        for pattern in cls.INJECTION_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return True, match.group(0)
        return False, None
