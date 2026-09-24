"""
SHIVANI Command Safety & Validation Pipeline
Performs lexical tokenization, argument checking, privilege boundary inspection,
and sandbox safety evaluation before executing any shell commands.
"""

from enum import Enum
import os
from pathlib import Path
import re
import shlex
from typing import Dict, List, Optional, Set, Tuple


class CommandStatus(str, Enum):
    SAFE = "SAFE"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    BLOCKED = "BLOCKED"


class CommandPolicy:
    """Configurable boundaries for shell command execution."""

    SAFE_EXECUTABLES: Set[str] = {
        "git", "python", "py", "pytest", "npm", "node", "pip", "uv",
        "dir", "echo", "cat", "type", "where", "which", "findstr", "grep",
        "ls", "pwd", "tree", "hostname", "whoami",
    }

    BLOCKED_PATTERNS: List[re.Pattern] = [
        re.compile(r"\b(?:format|diskpart|mkfs|dd\s+if=)\b", re.IGNORECASE),
        re.compile(r"\b(?:rmdir\s+/[sq]\s+[a-z]:\\|rm\s+-rf\s+(?:/|[a-z]:\\))\b", re.IGNORECASE),
        re.compile(r"\b(?:del|erase)\s+/[sfq]\s+[a-z]:\\windows\b", re.IGNORECASE),
        re.compile(r"\b(?:reg\s+(?:delete|add)|takeown|icacls\s+.*\/grant)\b", re.IGNORECASE),
        re.compile(r"\b(?:net\s+(?:user|localgroup)\s+.*\/add)\b", re.IGNORECASE),
        re.compile(r"\b(?:powershell(?:\.exe)?\s+(?:-enc|-encodedcommand))\b", re.IGNORECASE),
        re.compile(r"\b(?:bcdedit|vssadmin\s+delete\s+shadows)\b", re.IGNORECASE),
    ]

    APPROVAL_REQUIRED_PATTERNS: List[re.Pattern] = [
        re.compile(r"\bgit\s+(?:push|reset\s+--hard)\b", re.IGNORECASE),
        re.compile(r"\b(?:pip|npm|uv)\s+(?:install|uninstall)\b", re.IGNORECASE),
        re.compile(r"\b(?:shutdown|restart-computer|taskkill)\b", re.IGNORECASE),
    ]


class CommandRiskClassifier:
    @classmethod
    def evaluate(cls, command_str: str) -> Tuple[CommandStatus, str]:
        cmd_clean = command_str.strip()
        if not cmd_clean:
            return CommandStatus.SAFE, "Empty command"

        # 1. Check blocked destructive patterns
        for pattern in CommandPolicy.BLOCKED_PATTERNS:
            if pattern.search(cmd_clean):
                return CommandStatus.BLOCKED, f"Command matches blocked destructive pattern: {pattern.pattern}"

        # 2. Check approval required patterns
        for pattern in CommandPolicy.APPROVAL_REQUIRED_PATTERNS:
            if pattern.search(cmd_clean):
                return CommandStatus.REQUIRES_APPROVAL, f"Command matches sensitive pattern requiring confirmation: {pattern.pattern}"

        # 3. Lexical inspection of primary executable
        try:
            tokens = shlex.split(cmd_clean, posix=False)
        except Exception:
            tokens = cmd_clean.split()

        if not tokens:
            return CommandStatus.SAFE, "Empty tokens"

        exe = Path(tokens[0]).name.lower().replace(".exe", "")

        # Safe read-only or testing commands
        if exe in CommandPolicy.SAFE_EXECUTABLES:
            # Check for dangerous arguments inside safe commands
            if exe == "git" and any(arg.lower() in ("push", "--force") for arg in tokens):
                return CommandStatus.REQUIRES_APPROVAL, "Git push operations require explicit approval."
            return CommandStatus.SAFE, f"Executable '{exe}' is in safe list."

        # Default fallback: external arbitrary scripts require approval
        return CommandStatus.REQUIRES_APPROVAL, f"Executable '{exe}' is not pre-cleared as SAFE."


class CommandValidator:
    """Validates commands against working directory boundaries and security policies."""

    def __init__(self, allowed_directories: Optional[List[str]] = None):
        self.allowed_dirs = [os.path.normpath(os.path.abspath(d)) for d in (allowed_directories or [os.getcwd()])]

    def is_working_dir_allowed(self, cwd: str) -> bool:
        norm_cwd = os.path.normpath(os.path.abspath(cwd))
        # Allow if under any configured allowed directory
        return any(norm_cwd.startswith(allowed) for allowed in self.allowed_dirs)

    def validate(self, command: str, cwd: Optional[str] = None) -> Tuple[bool, CommandStatus, str]:
        if cwd and not self.is_working_dir_allowed(cwd):
            return False, CommandStatus.BLOCKED, f"Working directory '{cwd}' is outside authorized filesystem boundaries."

        status, reason = CommandRiskClassifier.evaluate(command)
        if status == CommandStatus.BLOCKED:
            return False, CommandStatus.BLOCKED, reason

        return True, status, reason
