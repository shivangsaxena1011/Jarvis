"""
Unit tests for Phase 17 Terminal Autonomy, Command Safety Classifier, and Clipboard Privacy.
"""

import pytest
from core.computer.models import CommandRisk
from core.computer.observation_engine import ObservationEngine
from core.computer.terminal_controller import (
    TerminalController,
    TerminalSafetyClassifier,
)
from tools.desktop.os.mock import MockOperatingSystemAdapter


def test_command_safety_classification():
    classifier = TerminalSafetyClassifier()

    # Safe commands
    assert classifier.classify("pytest -v tests/") == CommandRisk.SAFE
    assert classifier.classify("git status") == CommandRisk.SAFE
    assert classifier.classify("python --version") == CommandRisk.SAFE
    assert classifier.classify("dir") == CommandRisk.SAFE

    # Dangerous commands
    assert classifier.classify("del /f /q old_data.txt") == CommandRisk.DANGEROUS
    assert classifier.classify("rm -rf temp_dir") == CommandRisk.DANGEROUS
    assert classifier.classify("shutdown /s /t 0") == CommandRisk.DANGEROUS

    # Prohibited commands
    assert classifier.classify("rm -rf /") == CommandRisk.PROHIBITED
    assert classifier.classify("del C:\\Windows\\System32\\*") == CommandRisk.PROHIBITED


@pytest.mark.asyncio
async def test_terminal_dangerous_command_blocked():
    terminal = TerminalController()

    with pytest.raises(PermissionError) as exc_info:
        await terminal.execute_command("del myfile.txt", user_approved=False)
    assert "classified as DANGEROUS and requires explicit user confirmation" in str(exc_info.value)


@pytest.mark.asyncio
async def test_terminal_safe_command_execution():
    terminal = TerminalController()
    res = await terminal.execute_command("python --version")

    assert res.success is True
    assert res.exit_code == 0
    assert "Python" in res.stdout or "Python" in res.stderr
    assert res.risk == CommandRisk.SAFE


@pytest.mark.asyncio
async def test_clipboard_privacy_redaction():
    mock_os = MockOperatingSystemAdapter()
    await mock_os.clipboard_write("bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.secret_token")

    obs_engine = ObservationEngine(os_adapter=mock_os)
    obs = await obs_engine.observe(capture_image=False)

    assert obs.clipboard_is_sensitive is True
    assert obs.clipboard_text == "[REDACTED_SENSITIVE_CLIPBOARD]"
