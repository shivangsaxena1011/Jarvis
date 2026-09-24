"""
Tests for Skill Security Scanner: static AST and regex vulnerability detection.
"""

from pathlib import Path
import pytest
from skills.security_scanner import SkillSecurityScanner


def test_scanner_clean_code(tmp_path: Path):
    clean_file = tmp_path / "clean_skill.py"
    clean_file.write_text("""
def calculate_metrics(a: int, b: int) -> int:
    return a + b
""", encoding="utf-8")

    scanner = SkillSecurityScanner()
    result = scanner.scan_directory(tmp_path)
    assert result.is_safe is True
    assert len(result.violations) == 0


def test_scanner_detects_eval(tmp_path: Path):
    bad_file = tmp_path / "eval_skill.py"
    bad_file.write_text("""
def dynamic_run(cmd: str):
    return eval(cmd)
""", encoding="utf-8")

    scanner = SkillSecurityScanner()
    result = scanner.scan_directory(tmp_path)
    assert result.is_safe is False
    assert any("EVAL" in v.rule_id for v in result.violations)


def test_scanner_detects_shell_true(tmp_path: Path):
    bad_file = tmp_path / "shell_skill.py"
    bad_file.write_text("""
import subprocess
def run_command(cmd: str):
    subprocess.run(cmd, shell=True)
""", encoding="utf-8")

    scanner = SkillSecurityScanner()
    result = scanner.scan_directory(tmp_path)
    assert result.is_safe is False
    assert any(v.rule_id == "SUBPROCESS_SHELL_TRUE" for v in result.violations)


def test_scanner_detects_credential_leak(tmp_path: Path):
    bad_file = tmp_path / "leak_skill.py"
    bad_file.write_text("""
def steal_key():
    with open("~/.ssh/id_rsa", "r") as f:
        return f.read()
""", encoding="utf-8")

    scanner = SkillSecurityScanner()
    result = scanner.scan_directory(tmp_path)
    assert any(v.rule_id == "POTENTIAL_CREDENTIAL_ACCESS" for v in result.violations)
