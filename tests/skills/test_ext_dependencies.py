"""
Tests for Skill Dependency Resolver: missing dependencies, cycles, and Kahn's sort.
"""

import pytest
from skills.dependency_resolver import DependencyResolver
from skills.manifest import SkillEntrypoint, SkillManifest


def make_manifest(name: str, deps: list[str]) -> SkillManifest:
    return SkillManifest(
        name=name,
        display_name=name.capitalize(),
        version="1.0.0",
        description="Dependency test",
        dependencies=deps,
        entrypoint=SkillEntrypoint(module="m", class_name="C"),
    )


def test_dependency_resolution_clean_order():
    m_base = make_manifest("base_tool", [])
    m_mid = make_manifest("mid_tool", ["base_tool"])
    m_top = make_manifest("top_tool", ["mid_tool"])

    resolver = DependencyResolver({
        "base_tool": m_base,
        "mid_tool": m_mid,
        "top_tool": m_top,
    })

    result = resolver.resolve(["top_tool"])
    assert result.is_valid is True
    assert result.install_order == ["base_tool", "mid_tool", "top_tool"]
    assert len(result.errors) == 0


def test_dependency_resolution_missing():
    m = make_manifest("orphan", ["non_existent_skill_xyz"])
    resolver = DependencyResolver({"orphan": m})

    result = resolver.resolve(["orphan"])
    assert result.is_valid is False
    assert len(result.missing_dependencies) > 0


def test_dependency_resolution_circular():
    m_a = make_manifest("skill_a", ["skill_b"])
    m_b = make_manifest("skill_b", ["skill_a"])

    resolver = DependencyResolver({
        "skill_a": m_a,
        "skill_b": m_b,
    })

    result = resolver.resolve(["skill_a", "skill_b"])
    assert result.is_valid is False
    assert len(result.cyclic_dependencies) > 0
    assert any("Circular dependency" in err for err in result.errors)
