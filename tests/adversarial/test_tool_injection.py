"""
Red-Team Adversarial Matrix: Tool Injection & Destructive Action Defenses (Phase 20)
Verifies prevention of destructive system commands, filesystem escape attacks,
and unauthorized privileged tool invocations.
"""

from pathlib import Path
import tempfile
import pytest

from security.sandbox import CommandValidator, CommandRisk
from security.filesystem_safety import PathValidator, FilesystemPolicy
from security.permissions.models import RiskLevel, ApprovalScope
from security.permissions.engine import PermissionEngine


def test_destructive_shell_commands_strictly_blocked():
    """Verifies that high-risk destructive operating system commands are blocked unconditionally."""
    destructive_payloads = [
        "rm -rf /",
        "rmdir /s /q C:\\",
        "format C: /y",
        "diskpart /s clean.txt",
        "del /f /s /q C:\\Windows\\System32",
        "shutdown /s /t 0",
        "bcdedit /delete {current}",
        ":(){ :|:& };:",
        "mkfs.ext4 /dev/sda1",
        "dd if=/dev/zero of=/dev/sda",
    ]

    for cmd in destructive_payloads:
        risk = CommandValidator.classify_command(cmd)
        is_blocked, reason = CommandValidator.is_blocked(cmd)
        assert risk == CommandRisk.BLOCKED, f"Command should be BLOCKED: {cmd}"
        assert is_blocked is True
        assert len(reason) > 0


def test_filesystem_boundary_escape_and_traversal_blocked():
    """Verifies that path traversal attacks attempting to break out of safe working directory are rejected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox_root = Path(tmpdir).resolve()
        sub_workspace = sandbox_root / "workspace"
        sub_workspace.mkdir()

        # Malicious traversal attempts
        escapes = [
            sandbox_root / ".." / "system_sensitive.txt",
            sandbox_root / "workspace" / ".." / ".." / "boot.ini",
            Path(r"C:\Windows\System32\drivers\etc\hosts"),
            Path(r"C:\Windows\System32\cmd.exe"),
        ]

        for escape_target in escapes:
            valid, err = PathValidator.validate_within_boundary(sub_workspace, escape_target)
            assert valid is False, f"Traversal should be blocked: {escape_target}"
            assert err is not None


@pytest.mark.asyncio
async def test_tool_permission_enforcement_fail_closed():
    """Verifies that sensitive/critical tools fail-closed without explicit user approval."""
    engine = PermissionEngine(policy="strict")
    task_id = "test-jailbreak-task"

    # Attacker tries to execute high-risk tool without approval
    authorized = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name="terminal_execute",
        arguments={"cmd": "format D:"},
        default_risk=RiskLevel.CRITICAL,
        description="Format secondary drive",
        timeout_seconds=0.05
    )
    # Must fail closed (False)
    assert authorized is False
