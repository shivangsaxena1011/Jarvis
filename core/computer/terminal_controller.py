"""
SHIVANI Terminal Autonomy & Command Safety Classifier (Phase 17).
Provides safe command execution, multi-tier risk classification,
terminal output capture, and error diagnostic parsing.
"""

from __future__ import annotations
import asyncio
import os
import re
import shlex
import subprocess
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from core.computer.models import CommandRisk


class TerminalExecutionResult(BaseModel):
    command: str
    risk: CommandRisk
    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float
    parsed_diagnostics: Dict[str, Any] = Field(default_factory=dict)
    success: bool = True


class TerminalSafetyClassifier:
    """Classifies CLI commands into risk categories: SAFE, SENSITIVE, DANGEROUS, PROHIBITED."""

    SAFE_PATTERNS = [
        r"^git\s+(status|log|diff|branch|show|help)",
        r"^(pytest|python\s+-m\s+pytest)",
        r"^(npm|yarn|pnpm)\s+(test|run\s+test|run\s+lint)",
        r"^(python|python3|node|cargo|rustc|go|uv)\s+(--version|-v)",
        r"^(dir|ls|pwd|echo|type|cat|head|tail|grep|findstr)",
        r"^(uv\s+run|uv\s+pip\s+list)",
    ]

    DANGEROUS_PATTERNS = [
        r"\b(rm|rmdir|del|erase)\b",
        r"\b(format|diskpart|fdisk|mkfs)\b",
        r"\b(reg\s+delete|reg\s+add)\b",
        r"\b(shutdown|reboot|poweroff)\b",
        r"\b(net\s+user|net\s+localgroup)\b",
        r"\b(curl|wget)\b.*\|\s*(sh|bash|powershell|cmd)",
        r"\b(drop\s+database|truncate\s+table)\b",
    ]

    PROHIBITED_PATTERNS = [
        r"del\s+.*[cC]:\\(windows|system32)",
        r"format\s+[cC]:",
        r"rm\s+-rf\s+/",
        r"vssadmin\s+delete\s+shadows",
    ]

    @classmethod
    def classify(cls, command: str) -> CommandRisk:
        cmd = command.strip()
        for pat in cls.PROHIBITED_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return CommandRisk.PROHIBITED

        for pat in cls.DANGEROUS_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return CommandRisk.DANGEROUS

        for pat in cls.SAFE_PATTERNS:
            if re.search(pat, cmd, re.IGNORECASE):
                return CommandRisk.SAFE

        # Default fallback for unknown shell commands is SENSITIVE
        return CommandRisk.SENSITIVE


class TerminalController:
    """Controls terminal execution with strict safety enforcement and diagnostics."""

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.classifier = TerminalSafetyClassifier()

    def classify_command(self, command: str) -> CommandRisk:
        return self.classifier.classify(command)

    async def execute_command(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_seconds: float = 60.0,
        user_approved: bool = False,
    ) -> TerminalExecutionResult:
        """
        Executes a terminal command safely if risk rules are satisfied.
        """
        risk = self.classify_command(command)
        if risk == CommandRisk.PROHIBITED:
            raise PermissionError(f"Command '{command}' is strictly prohibited by security policy.")

        if risk == CommandRisk.DANGEROUS and not user_approved:
            raise PermissionError(
                f"Command '{command}' is classified as DANGEROUS and requires explicit user confirmation."
            )

        effective_cwd = cwd or self.working_dir
        start_time = asyncio.get_event_loop().time()

        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=effective_cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_seconds
            )
            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = proc.returncode or 0
        except asyncio.TimeoutError:
            proc.kill()
            stdout = ""
            stderr = f"Command timed out after {timeout_seconds} seconds."
            exit_code = -1

        duration = asyncio.get_event_loop().time() - start_time
        success = exit_code == 0

        # Parse diagnostics
        diagnostics = self._parse_diagnostics(command, stdout, stderr, exit_code)

        return TerminalExecutionResult(
            command=command,
            risk=risk,
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            duration_seconds=duration,
            parsed_diagnostics=diagnostics,
            success=success,
        )

    def _parse_diagnostics(
        self, command: str, stdout: str, stderr: str, exit_code: int
    ) -> Dict[str, Any]:
        diag: Dict[str, Any] = {"exit_code": exit_code}
        combined = (stdout + "\n" + stderr).lower()

        # Pytest parser
        if "pytest" in command:
            if "failed" in combined:
                diag["test_status"] = "FAILURES_DETECTED"
                failures = re.findall(r"FAILED\s+([^\s]+)", stdout + stderr)
                diag["failed_tests"] = failures
            elif "passed" in combined:
                diag["test_status"] = "ALL_PASSED"

        # Missing dependency parser
        if "modulenotfounderror" in combined or "cannot find module" in combined:
            diag["error_type"] = "MISSING_DEPENDENCY"
            m = re.search(r"no module named ['\"]([^'\"]+)['\"]", combined)
            if m:
                diag["missing_module"] = m.group(1)

        # Syntax error
        if "syntaxerror" in combined:
            diag["error_type"] = "SYNTAX_ERROR"

        return diag
