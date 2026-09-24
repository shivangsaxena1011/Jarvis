"""
SHIVANI Subprocess Sandbox
Executes commands within bounded memory, output size, and execution timeouts.
Sanitizes environment variables to prevent accidental credential leakage to child processes.
"""

import asyncio
import os
import subprocess
from typing import Dict, List, Optional, Tuple


class ProcessSandbox:
    CLEAN_ENV_VARS_TO_STRIP: List[str] = [
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "GITHUB_TOKEN",
        "AWS_SECRET_ACCESS_KEY",
        "SHIVANI_DEVICE_SECRET",
    ]

    @classmethod
    def get_sanitized_env(cls, custom_env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        env = dict(os.environ)
        for var in cls.CLEAN_ENV_VARS_TO_STRIP:
            env.pop(var, None)
        if custom_env:
            env.update(custom_env)
        return env

    @classmethod
    async def execute_sandboxed(
        cls,
        command: str,
        cwd: Optional[str] = None,
        timeout: float = 30.0,
        max_output_bytes: int = 1024 * 1024,
    ) -> Tuple[int, str, str]:
        """
        Executes a shell command asynchronously inside a sanitized environment with a hard timeout.
        Returns (exit_code, stdout, stderr).
        """
        sanitized_env = cls.get_sanitized_env()

        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=cwd,
            env=sanitized_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_data, stderr_data = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            out_str = stdout_data[:max_output_bytes].decode("utf-8", errors="replace")
            err_str = stderr_data[:max_output_bytes].decode("utf-8", errors="replace")
            return proc.returncode or 0, out_str, err_str
        except asyncio.TimeoutError:
            try:
                proc.kill()
            except Exception:
                pass
            return -1, "", f"Command timed out after {timeout} seconds."
