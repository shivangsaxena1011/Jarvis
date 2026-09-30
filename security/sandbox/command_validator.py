"""
SHIVANI Sandbox & Command Validator
Inspects commands and file paths for security threats, destructive operations,
and path traversal attacks using a 4-tier classification: SAFE, WARNING, DANGEROUS, BLOCKED.
"""

from enum import Enum
import re
from pathlib import Path
from typing import Tuple
from security.permissions.engine import RiskLevel


class CommandRisk(str, Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    DANGEROUS = "DANGEROUS"
    BLOCKED = "BLOCKED"


# Patterns strictly blocked under any circumstance
BLOCKED_PATTERNS = [
    r"\bformat\s+[a-zA-Z]:",
    r"\bdiskpart\b",
    r"\bbcdedit\b",
    r"\brmdir\s+/[sS]\s+/[qQ]\s+[cC]:\\",
    r"\bdel\s+/[fF]\s+/[sS]\s+/[qQ]\s+[cC]:\\",
    r"\brm\s+-rf\s+/(?:\s|$)",
    r"\bshutdown\s+/[sSrR]",
    r"\breg\s+delete\s+HKLM",
    r"\bmkfs(?:\.[a-zA-Z0-9]+)?\b",
    r"\bdd\s+if=",
    r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", # bash fork bomb
    r"%0\|%0",                                   # batch fork bomb
]

# Patterns that are DANGEROUS (deletions, process termination, remote script execution)
DANGEROUS_PATTERNS = [
    r"\bdel\b",
    r"\brmdir\b",
    r"\brm\s+",
    r"\bkill\b",
    r"\btaskkill\s+/[fF]",
    r"\bnet\s+user\b",
    r"\bInvoke-Expression\b",
    r"\biex\b",
    r"\bcurl.*\|\s*(?:bash|sh|powershell|cmd)",
    r"\bwget.*\|\s*(?:bash|sh|powershell|cmd)",
]

# Patterns that are WARNING (active modifications / builds / commits)
WARNING_PATTERNS = [
    r"\bpython\b",
    r"\bpython3\b",
    r"\buv\b",
    r"\bpip\b",
    r"\bgit\s+(?:push|commit|checkout|merge|rebase|reset)",
    r"\bnpm\b",
    r"\bnode\b",
    r"\bcargo\b",
]

# Patterns that are SAFE (read-only inspection)
SAFE_PATTERNS = [
    r"^(?:dir|ls|echo|type|cat|pwd|whoami|git\s+status|git\s+diff|git\s+log|where|which)(?:\s|$)",
    r"^python\s+--(?:version|help)",
    r"^git\s+--(?:version|help)",
]


class CommandValidator:
    """Validates and classifies shell commands before execution."""

    @staticmethod
    def is_blocked(command: str) -> Tuple[bool, str]:
        cmd_clean = command.strip()
        for pattern in BLOCKED_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return True, f"Command contains blocked destructive pattern: {pattern}"
        return False, ""

    @staticmethod
    def classify_command(command: str) -> CommandRisk:
        """Classifies command into SAFE, WARNING, DANGEROUS, or BLOCKED."""
        cmd_clean = command.strip()
        
        # 1. BLOCKED check
        blocked, _ = CommandValidator.is_blocked(cmd_clean)
        if blocked:
            return CommandRisk.BLOCKED

        # 2. DANGEROUS check
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return CommandRisk.DANGEROUS

        # 3. SAFE check
        for pattern in SAFE_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return CommandRisk.SAFE

        # 4. WARNING check (default for mutating commands)
        for pattern in WARNING_PATTERNS:
            if re.search(pattern, cmd_clean, re.IGNORECASE):
                return CommandRisk.WARNING

        return CommandRisk.WARNING

    @staticmethod
    def classify_risk(command: str) -> RiskLevel:
        """Translates command risk into permission RiskLevel."""
        c_risk = CommandValidator.classify_command(command)
        if c_risk in (CommandRisk.BLOCKED, CommandRisk.DANGEROUS):
            return RiskLevel.CRITICAL
        elif c_risk == CommandRisk.WARNING:
            return RiskLevel.SENSITIVE
        return RiskLevel.SAFE

    @staticmethod
    def validate_path_safety(base_dir: Path, target_path: Path) -> Tuple[bool, str]:
        """Validates that target_path does not escape outside base_dir (path traversal check)."""
        try:
            resolved_base = base_dir.resolve()
            resolved_target = target_path.resolve()
            # Use relative_to() for correct boundary check (not string prefix)
            try:
                resolved_target.relative_to(resolved_base)
            except ValueError:
                return False, f"Path traversal detected: {target_path} escapes workspace {base_dir}"
            return True, ""
        except Exception as e:
            return False, f"Path resolution error: {e}"
