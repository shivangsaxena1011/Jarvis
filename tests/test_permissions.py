"""
Unit tests for SHIVANI Security & Permissions Engine.
"""

import pytest
from pathlib import Path
from security.permissions.engine import PermissionEngine, RiskLevel, ApprovalStatus
from security.sandbox.command_validator import CommandValidator, CommandRisk


def test_command_risk_classification():
    # 4-tier classifier checks
    assert CommandValidator.classify_command("dir") == CommandRisk.SAFE
    assert CommandValidator.classify_command("git status") == CommandRisk.SAFE
    assert CommandValidator.classify_command("python --version") == CommandRisk.SAFE

    assert CommandValidator.classify_command("pip install pydantic") == CommandRisk.WARNING
    assert CommandValidator.classify_command("python script.py") == CommandRisk.WARNING
    assert CommandValidator.classify_command("git commit -m 'test'") == CommandRisk.WARNING

    assert CommandValidator.classify_command("del test.txt") == CommandRisk.DANGEROUS
    assert CommandValidator.classify_command("taskkill /f /im notepad.exe") == CommandRisk.DANGEROUS

    assert CommandValidator.classify_command("format c:") == CommandRisk.BLOCKED
    assert CommandValidator.classify_command("rmdir /s /q c:\\") == CommandRisk.BLOCKED

    # Permission RiskLevel translation
    assert CommandValidator.classify_risk("dir") == RiskLevel.SAFE
    assert CommandValidator.classify_risk("pip install pydantic") == RiskLevel.SENSITIVE
    assert CommandValidator.classify_risk("del test.txt") == RiskLevel.CRITICAL



def test_blocked_destructive_commands():
    blocked1, reason1 = CommandValidator.is_blocked("format c:")
    assert blocked1 is True
    assert "format" in reason1

    blocked2, _ = CommandValidator.is_blocked("rmdir /s /q c:\\")
    assert blocked2 is True

    blocked3, _ = CommandValidator.is_blocked("rm -rf /")
    assert blocked3 is True

    # Safe command should not be blocked
    blocked4, _ = CommandValidator.is_blocked("echo hello world")
    assert blocked4 is False


def test_path_traversal_protection(tmp_path):
    base_dir = tmp_path / "workspace"
    base_dir.mkdir()

    safe_target = base_dir / "docs" / "readme.txt"
    is_safe, _ = CommandValidator.validate_path_safety(base_dir, safe_target)
    assert is_safe is True

    unsafe_target = base_dir / ".." / ".." / "windows" / "system32"
    is_safe, msg = CommandValidator.validate_path_safety(base_dir, unsafe_target)
    assert is_safe is False
    assert "Path traversal" in msg


@pytest.mark.asyncio
async def test_permission_approval_flow():
    engine = PermissionEngine(policy="strict")
    
    # Safe tool requires no approval
    safe_ok = await engine.evaluate_and_request(
        task_id="t1",
        tool_name="test.safe",
        arguments={},
        default_risk=RiskLevel.SAFE,
        description="Safe test"
    )
    assert safe_ok is True

    # SENSITIVE requires approval in strict mode
    async def request_sensitive():
        return await engine.evaluate_and_request(
            task_id="t2",
            tool_name="test.sensitive",
            arguments={"param": "value"},
            default_risk=RiskLevel.SENSITIVE,
            description="Sensitive test",
            timeout_seconds=5.0
        )

    import asyncio
    task_future = asyncio.create_task(request_sensitive())
    await asyncio.sleep(0.05)

    pending = engine.list_pending_requests()
    assert len(pending) == 1
    req = pending[0]
    assert req.status == ApprovalStatus.PENDING
    assert req.risk_level == RiskLevel.SENSITIVE

    # Resolve approval
    engine.resolve_request(req.id, approved=True, resolved_by="tester")
    result = await task_future
    assert result is True
