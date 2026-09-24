"""
SHIVANI Test & Build Runner
Executes native project test and build suites, captures stdout/stderr,
and parses test execution summaries.
"""

import asyncio
import re
import time
from pathlib import Path
from typing import List, Optional

from agents.coding.models import BuildResult, TestResult


class TestRunner:
    """Executes native test suites safely within project boundaries."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    async def run_tests(
        self,
        command: Optional[str] = None,
        test_path: Optional[str] = None,
        timeout_seconds: float = 60.0
    ) -> TestResult:
        """Executes test runner and parses output."""
        cmd = command or "pytest"
        if test_path:
            cmd += f" {test_path}"

        start_time = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_shell(
                cmd,
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            stdout = stdout_bytes.decode("utf-8", errors="replace")
            stderr = stderr_bytes.decode("utf-8", errors="replace")
            exit_code = proc.returncode if proc.returncode is not None else 1

            passed_count = 0
            failed_count = 0
            failed_tests: List[str] = []

            # Parse Pytest results
            py_pass = re.search(r"(\d+)\s+passed", stdout)
            py_fail = re.search(r"(\d+)\s+failed", stdout)
            if py_pass:
                passed_count = int(py_pass.group(1))
            if py_fail:
                failed_count = int(py_fail.group(1))

            # Parse failed test identifiers
            for line in stdout.splitlines():
                if line.startswith("FAILED ") or line.startswith("FAIL "):
                    failed_tests.append(line.replace("FAILED ", "").replace("FAIL ", "").split()[0])

            # Parse Jest / Vitest
            if not py_pass and not py_fail:
                jest_pass = re.search(r"Tests:\s+(\d+)\s+passed", stdout)
                jest_fail = re.search(r"Tests:\s+(\d+)\s+failed", stdout)
                if jest_pass:
                    passed_count = int(jest_pass.group(1))
                if jest_fail:
                    failed_count = int(jest_fail.group(1))

            success = (exit_code == 0) and (failed_count == 0)
            return TestResult(
                command=cmd,
                success=success,
                exit_code=exit_code,
                passed_count=passed_count,
                failed_count=failed_count,
                stdout=stdout,
                stderr=stderr,
                failed_tests=failed_tests,
                execution_time_ms=round(elapsed_ms, 2)
            )

        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TestResult(
                command=cmd,
                success=False,
                exit_code=-1,
                stderr=f"Test execution timed out after {timeout_seconds} seconds.",
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return TestResult(
                command=cmd,
                success=False,
                exit_code=-1,
                stderr=str(e),
                execution_time_ms=round(elapsed_ms, 2)
            )


class BuildRunner:
    """Executes project build or typecheck pipelines."""

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()

    async def run_build(self, command: str, timeout_seconds: float = 90.0) -> BuildResult:
        """Executes build or typecheck command."""
        start_time = time.perf_counter()
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=str(self.project_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0

            exit_code = proc.returncode if proc.returncode is not None else 1
            return BuildResult(
                command=command,
                success=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout_bytes.decode("utf-8", errors="replace"),
                stderr=stderr_bytes.decode("utf-8", errors="replace"),
                execution_time_ms=round(elapsed_ms, 2)
            )
        except Exception as e:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return BuildResult(
                command=command,
                success=False,
                exit_code=-1,
                stderr=str(e),
                execution_time_ms=round(elapsed_ms, 2)
            )
