"""
Tests for Skill Registry: action indexing, searching, and Tool/Agent synchronization.
"""

import pytest
from core.agents.registry import AgentRegistry
from tools.base import BaseTool, ToolResult
from tools.registry import ToolRegistry
from skills.manifest import SkillEntrypoint, SkillManifest
from skills.models import ActionSchema, ActionVerb, SkillState
from skills.registry import SkillRegistry
from skills.runtime import BaseSkill


class SampleTool(BaseTool):
    name = "sample_skill_tool"
    description = "Sample skill tool for registry testing"

    async def run(self, **kwargs):
        return ToolResult(success=True, data="sample_output")


class SampleSkill(BaseSkill):
    async def initialize(self):
        self.state = SkillState.ACTIVE

    async def shutdown(self):
        self.state = SkillState.DISABLED

    def get_tools(self):
        return [SampleTool()]


def test_skill_registry_mounting_and_cleanup():
    tools = ToolRegistry()
    agents = AgentRegistry()
    registry = SkillRegistry(tool_registry=tools, agent_registry=agents)

    manifest = SkillManifest(
        name="sample_skill",
        display_name="Sample Skill",
        version="1.0.0",
        description="A sample registry skill",
        tags=["automation", "utilities"],
        capabilities=[
            ActionSchema(name="sample_act", verb=ActionVerb.EXECUTE, description="Executes sample action")
        ],
        entrypoint=SkillEntrypoint(module="m", class_name="C"),
    )
    skill = SampleSkill(manifest=manifest)

    # 1. Register skill
    registry.register_skill(skill)
    assert registry.get_skill("sample_skill") is not None
    assert tools.get_tool("sample_skill_tool") is not None  # Auto-mounted!

    # 2. Action finding
    match = registry.find_action("sample_act")
    assert match is not None
    found_skill, schema = match
    assert found_skill.name == "sample_skill"
    assert schema.name == "sample_act"

    # 3. Query search
    query_res = registry.find_skills_by_query("automation")
    assert len(query_res) == 1
    assert query_res[0].name == "sample_skill"

    # 4. Unregister cleanup
    unreg = registry.unregister_skill("sample_skill")
    assert unreg is True
    assert registry.get_skill("sample_skill") is None
    assert tools.get_tool("sample_skill_tool") is None  # Auto-unmounted!
