"""
Tests for Skill Sandbox: execution timeout, crash containment, and boundary checks.
"""

import asyncio
from pathlib import Path
import pytest

from skills.manifest import SkillEntrypoint, SkillManifest, SkillPolicies
from skills.sandbox import SandboxSecurityError, SkillSandbox


def make_sandbox(tmp_path: Path, timeout: float = 0.5) -> SkillSandbox:
    manifest = SkillManifest(
        name="test_sandbox_skill",
        display_name="Sandbox Skill",
        version="1.0.0",
        description="Testing sandbox limits",
        policies=SkillPolicies(timeout_seconds=timeout),
        entrypoint=SkillEntrypoint(module="m", class_name="C"),
    )
    sandbox = SkillSandbox(manifest, allowed_paths=[tmp_path], allowed_domains=["api.github.com"])
    return sandbox


@pytest.mark.asyncio
async def test_sandbox_timeout_enforcement(tmp_path: Path):
    sandbox = make_sandbox(tmp_path, timeout=0.1)

    async def slow_work():
        await asyncio.sleep(0.5)
        return "completed"

    res = await sandbox.execute_coroutine(slow_work)
    assert res.is_err is True
    assert isinstance(res.unwrap_err(), TimeoutError)
    assert sandbox.telemetry.errors == 1


@pytest.mark.asyncio
async def test_sandbox_crash_containment(tmp_path: Path):
    sandbox = make_sandbox(tmp_path, timeout=1.0)

    async def crashing_work():
        raise ZeroDivisionError("Simulated skill crash")

    res = await sandbox.execute_coroutine(crashing_work)
    assert res.is_err is True
    assert isinstance(res.unwrap_err(), ZeroDivisionError)
    assert sandbox.telemetry.errors == 1


def test_sandbox_path_containment(tmp_path: Path):
    sandbox = make_sandbox(tmp_path)
    allowed_file = tmp_path / "data.txt"
    sandbox.validate_path_access(allowed_file)  # Should not raise

    unauthorized_file = Path("C:/Windows/System32/calc.exe")
    with pytest.raises(SandboxSecurityError):
        sandbox.validate_path_access(unauthorized_file)


def test_sandbox_network_containment(tmp_path: Path):
    sandbox = make_sandbox(tmp_path)
    sandbox.validate_network_access("https://api.github.com/repos")  # Should not raise

    with pytest.raises(SandboxSecurityError):
        sandbox.validate_network_access("https://malicious-exfiltration.com/log")
