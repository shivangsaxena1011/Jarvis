"""
SHIVANI Terminal & Shell Tools
Provides controlled shell command execution with security risk classification,
sandboxing, and output capture.
"""

import asyncio
import subprocess
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from security.sandbox.command_validator import CommandValidator


class TerminalExecuteArgs(BaseModel):
    command: str = Field(description="The shell command line to execute")
    cwd: Optional[str] = Field(default=None, description="Working directory for the command")
    timeout_seconds: float = Field(default=30.0, description="Max execution time in seconds")


class TerminalExecuteTool(BaseTool):
    name = "terminal.execute"
    description = "Execute a shell command with security validation and sandbox policy checks."
    permission_level = RiskLevel.SENSITIVE
    args_schema = TerminalExecuteArgs

    async def run(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_seconds: float = 30.0
    ) -> Dict[str, Any]:
        # 1. Sandboxing Check: blocked commands
        blocked, reason = CommandValidator.is_blocked(command)
        if blocked:
            raise PermissionError(f"Security Sandbox Violation: {reason}")

        # 2. Dynamic risk level calculation
        risk = CommandValidator.classify_risk(command)
        self.permission_level = risk

        # 3. Asynchronous Subprocess Execution
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_seconds
            )
            return {
                "command": command,
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace").strip(),
                "stderr": stderr.decode("utf-8", errors="replace").strip(),
                "cwd": cwd or "."
            }
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except ProcessLookupError:
                pass
            raise TimeoutError(f"Command timed out after {timeout_seconds} seconds: {command}")

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        exit_code = result_data.get("exit_code", -1)
        return {
            "verified": exit_code == 0,
            "exit_code": exit_code,
            "has_error": exit_code != 0
        }
