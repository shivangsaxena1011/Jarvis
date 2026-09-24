"""
Tests for Skill Generator: scaffolding valid skill packages with code, manifest, and README.
"""

from pathlib import Path
import pytest
from skills.generator import SkillGenerator, SkillScaffoldRequest
from skills.validator import SkillValidator


def test_generator_scaffolding(tmp_path: Path):
    req = SkillScaffoldRequest(
        name="crypto_price",
        display_name="Crypto Price Checker",
        description="Checks Bitcoin and Ethereum prices in real time",
        category="finance",
        actions=[
            {"name": "get_price", "description": "Fetches current token price"}
        ],
        permissions=["network.read"],
    )

    out_dir = SkillGenerator.generate_skill(req, tmp_path)
    assert out_dir.exists()
    assert (out_dir / "manifest.json").exists()
    assert (out_dir / "skill.py").exists()
    assert (out_dir / "README.md").exists()

    # The scaffolded package MUST pass SkillValidator!
    val = SkillValidator.validate_package(out_dir)
    assert val.is_valid is True
    assert val.manifest is not None
    assert val.manifest.name == "crypto_price"
    assert len(val.manifest.actions) == 1
