"""
Tests for Skill Validator: semver, names, permissions, and directory structure.
"""

import json
from pathlib import Path
import pytest

from skills.validator import SkillValidator


def test_validator_valid_manifest():
    data = {
        "name": "weather_service",
        "display_name": "Weather Service",
        "version": "1.2.3",
        "description": "Fetches current weather",
        "permissions": ["network.read", "filesystem.read"],
        "entrypoint": {"module": "weather", "class_name": "WeatherSkill"},
    }
    is_valid, errors, manifest = SkillValidator.validate_manifest(data)
    assert is_valid is True
    assert len(errors) == 0
    assert manifest is not None
    assert manifest.name == "weather_service"


def test_validator_invalid_name():
    data = {
        "name": "Invalid Name!",
        "display_name": "Invalid",
        "version": "1.0.0",
        "description": "Desc",
        "entrypoint": {"module": "m", "class_name": "C"},
    }
    is_valid, errors, _ = SkillValidator.validate_manifest(data)
    assert is_valid is False
    assert any("Invalid skill name" in err for err in errors)


def test_validator_invalid_semver():
    data = {
        "name": "valid_name",
        "display_name": "Valid",
        "version": "v1.0-final",
        "description": "Desc",
        "entrypoint": {"module": "m", "class_name": "C"},
    }
    is_valid, errors, _ = SkillValidator.validate_manifest(data)
    assert is_valid is False
    assert any("Invalid semantic version" in err for err in errors)


def test_validator_package_directory(tmp_path: Path):
    pkg_dir = tmp_path / "valid_pkg"
    pkg_dir.mkdir()

    manifest_data = {
        "name": "valid_pkg",
        "display_name": "Valid Package",
        "version": "1.0.0",
        "description": "A valid test package",
        "permissions": ["github.read"],
        "entrypoint": {"module": "skill", "class_name": "ValidSkill"},
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")
    (pkg_dir / "skill.py").write_text("class ValidSkill: pass", encoding="utf-8")

    result = SkillValidator.validate_package(pkg_dir)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_missing_entrypoint_file(tmp_path: Path):
    pkg_dir = tmp_path / "incomplete_pkg"
    pkg_dir.mkdir()

    manifest_data = {
        "name": "incomplete_pkg",
        "display_name": "Incomplete Package",
        "version": "1.0.0",
        "description": "Missing file",
        "entrypoint": {"module": "missing_module", "class_name": "Skill"},
    }
    (pkg_dir / "manifest.json").write_text(json.dumps(manifest_data), encoding="utf-8")

    result = SkillValidator.validate_package(pkg_dir)
    assert result.is_valid is False
    assert any(e.field == "entrypoint" for e in result.errors)
