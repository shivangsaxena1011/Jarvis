"""
Tests for Skill Manifest parsing, actions, and policies.
"""

import pytest
from security.permissions.models import RiskLevel
from skills.manifest import SkillEntrypoint, SkillManifest, SkillPolicies
from skills.models import ActionSchema, ActionVerb


def test_manifest_creation_and_defaults():
    manifest = SkillManifest(
        name="test_skill",
        display_name="Test Skill",
        version="1.0.0",
        description="A test skill",
        permissions=["github.read", "filesystem.read"],
        capabilities=[
            ActionSchema(
                name="read_repo",
                verb=ActionVerb.READ,
                description="Reads repository files",
            )
        ],
    )

    assert manifest.name == "test_skill"
    assert manifest.version == "1.0.0"
    assert len(manifest.permissions) == 2
    assert len(manifest.actions) == 1
    assert manifest.actions[0].name == "read_repo"
    assert manifest.actions[0].verb == ActionVerb.READ
    assert manifest.policies.timeout_seconds == 30.0


def test_manifest_entrypoint_file_resolution():
    ep1 = SkillEntrypoint(module="my_skill", class_name="MySkill")
    assert ep1.entry_file == "my_skill.py"

    ep2 = SkillEntrypoint(module="mod", class_name="MySkill", file="custom_entry.py")
    assert ep2.entry_file == "custom_entry.py"


def test_manifest_dict_serialization():
    manifest = SkillManifest(
        name="json_skill",
        display_name="JSON Skill",
        version="0.2.1",
        description="Testing serialization",
        entrypoint=SkillEntrypoint(module="skill", class_name="Skill"),
    )
    d = manifest.to_dict()
    assert d["name"] == "json_skill"
    assert d["version"] == "0.2.1"
    assert d["entrypoint"]["class_name"] == "Skill"
