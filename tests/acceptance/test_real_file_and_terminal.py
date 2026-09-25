"""
Real-world File Safety & Terminal Command Acceptance Test (Phase 20.5)
Verifies path validation boundary enforcement, file operations,
harmless command output capture, and dangerous command blocking on the real machine.
"""

from pathlib import Path
import tempfile
import pytest

from security.filesystem_safety import PathValidator
from security.sandbox import CommandValidator, CommandRisk
from tools.terminal.shell_tools import TerminalExecuteTool


def test_real_filesystem_crud_and_boundary_safety():
    """Tests file creation, reading, renaming, copying, and deletion inside a boundary, and boundary escape blocking."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sandbox_dir = Path(tmpdir).resolve()

        # 1. Create file safely
        test_file = sandbox_dir / "acceptance_test.txt"
        test_file.write_text("Shivani 1.0 Acceptance Test Content", encoding="utf-8")
        assert test_file.exists()

        # 2. PathValidator permits within boundary
        valid, err = PathValidator.validate_within_boundary(sandbox_dir, test_file)
        assert valid is True
        assert not err

        # 3. Read content
        assert test_file.read_text(encoding="utf-8") == "Shivani 1.0 Acceptance Test Content"

        # 4. Rename file
        renamed_file = sandbox_dir / "acceptance_renamed.txt"
        test_file.rename(renamed_file)
        assert not test_file.exists()
        assert renamed_file.exists()

        # 5. Path traversal attempt must be blocked
        escape_target = sandbox_dir / ".." / "system_sensitive.txt"
        valid_escape, err_escape = PathValidator.validate_within_boundary(sandbox_dir, escape_target)
        assert valid_escape is False
        assert err_escape is not None

        # 6. Delete file
        renamed_file.unlink()
        assert not renamed_file.exists()


@pytest.mark.asyncio
async def test_real_terminal_harmless_command_execution():
    """Executes harmless real terminal commands on the host machine and validates output capture."""
    term = TerminalExecuteTool()

    # Test 1: Python version
    res_py = await term.run("python --version")
    assert res_py["exit_code"] == 0
    assert "Python" in (res_py.get("stdout") or res_py.get("stderr") or "")

    # Test 2: Git version
    res_git = await term.run("git --version")
    assert res_git["exit_code"] == 0
    assert "git version" in (res_git.get("stdout") or "").lower()

    # Test 3: Echo
    res_echo = await term.run("echo Shivani")
    assert res_echo["exit_code"] == 0
    assert "Shivani" in (res_echo.get("stdout") or "")


@pytest.mark.asyncio
async def test_real_terminal_blocks_destructive_commands():
    """Verifies TerminalExecuteTool blocks destructive commands on real host."""
    term = TerminalExecuteTool()
    blocked_commands = [
        "format C:",
        "diskpart",
        "rmdir /s /q C:\\Windows",
        ":(){ :|:& };:",
    ]
    for cmd in blocked_commands:
        with pytest.raises(PermissionError) as exc_info:
            await term.run(cmd)
        assert "Sandbox Violation" in str(exc_info.value)
