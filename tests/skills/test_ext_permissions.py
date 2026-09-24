"""
Tests for Skill Permissions: risk calculation, diffing, and escalation detection.
"""

import pytest
from security.permissions.models import RiskLevel
from skills.manifest import SkillEntrypoint, SkillManifest
from skills.permissions import SkillPermissionManager


def test_permission_risk_mapping():
    assert SkillPermissionManager.get_permission_risk("filesystem.read") == RiskLevel.SAFE
    assert SkillPermissionManager.get_permission_risk("filesystem.write") == RiskLevel.HIGH_RISK
    assert SkillPermissionManager.get_permission_risk("filesystem.delete") == RiskLevel.CRITICAL
    assert SkillPermissionManager.get_permission_risk("terminal.execute") == RiskLevel.CRITICAL


def test_calculate_overall_risk():
    perms = ["github.read", "filesystem.read"]
    assert SkillPermissionManager.calculate_skill_overall_risk(perms) == RiskLevel.SAFE

    perms.append("email.send")
    assert SkillPermissionManager.calculate_skill_overall_risk(perms) == RiskLevel.SENSITIVE

    perms.append("system.security")
    assert SkillPermissionManager.calculate_skill_overall_risk(perms) == RiskLevel.CRITICAL


def test_permission_diff_and_escalation():
    old_m = SkillManifest(
        name="test_skill",
        display_name="Test",
        version="1.0.0",
        description="Old",
        permissions=["github.read"],
        entrypoint=SkillEntrypoint(module="m", class_name="C"),
    )

    new_m = SkillManifest(
        name="test_skill",
        display_name="Test",
        version="1.1.0",
        description="New with escalation",
        permissions=["github.read", "filesystem.write", "terminal.execute"],
        entrypoint=SkillEntrypoint(module="m", class_name="C"),
    )

    diff = SkillPermissionManager.diff_permissions(old_m, new_m)
    assert diff.has_escalation is True
    assert "filesystem.write" in diff.added_permissions
    assert "terminal.execute" in diff.added_permissions
    assert diff.new_risk_level == RiskLevel.CRITICAL
