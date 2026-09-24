"""
SHIVANI Skill Registry
Maintains discovered, installed, and active skills, synchronizing tools with
ToolRegistry, agents with AgentRegistry, and indexing action verbs.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from core.agents.registry import AgentRegistry
from tools.registry import ToolRegistry
from skills.manifest import SkillManifest
from skills.models import ActionSchema, SkillHealth, SkillMetadata, SkillState
from skills.runtime import BaseSkill

logger = logging.getLogger("shivani.skills.registry")


class SkillRegistry:
    """Central registry for SHIVANI skills and their exposed capabilities."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        agent_registry: Optional[AgentRegistry] = None,
    ):
        self._skills: Dict[str, BaseSkill] = {}
        self._manifests: Dict[str, SkillManifest] = {}
        self._actions: Dict[str, Tuple[str, ActionSchema]] = {}  # action_name -> (skill_name, schema)
        self.tool_registry = tool_registry
        self.agent_registry = agent_registry

    def register_skill(self, skill: BaseSkill) -> None:
        """Registers a skill and mounts its tools and agents into system registries."""
        name = skill.name
        self._skills[name] = skill
        self._manifests[name] = skill.manifest

        # Index action verbs
        for action in skill.capabilities():
            self._actions[action.name] = (name, action)

        # Register tools into ToolRegistry if available
        if self.tool_registry:
            for tool in skill.get_tools():
                self.tool_registry.register(tool)
                logger.info(f"Mounted skill tool '{tool.name}' from skill '{name}'")

        # Register agents into AgentRegistry if available
        if self.agent_registry:
            for agent in skill.get_agents():
                if hasattr(agent, "descriptor"):
                    self.agent_registry.register_agent(agent.descriptor, agent)
                    logger.info(f"Mounted skill agent '{agent.descriptor.name}' from skill '{name}'")

        skill.state = SkillState.ACTIVE
        skill.metadata.state = SkillState.ACTIVE
        logger.info(f"Skill '{name}' (v{skill.version}) successfully registered and activated.")

    def unregister_skill(self, skill_name: str) -> bool:
        """Unregisters a skill and cleans up its tools and agents from system registries."""
        skill = self._skills.get(skill_name)
        if not skill:
            return False

        # Unregister tools
        if self.tool_registry:
            for tool in skill.get_tools():
                self.tool_registry.unregister(tool.name)
                logger.info(f"Unmounted skill tool '{tool.name}' from skill '{skill_name}'")

        # Unregister agents
        if self.agent_registry:
            for agent in skill.get_agents():
                if hasattr(agent, "descriptor"):
                    self.agent_registry.unregister_agent(agent.descriptor.name)
                    logger.info(f"Unmounted skill agent '{agent.descriptor.name}' from skill '{skill_name}'")

        # Clean up indexed actions
        actions_to_remove = [k for k, (s_name, _) in self._actions.items() if s_name == skill_name]
        for k in actions_to_remove:
            del self._actions[k]

        skill.state = SkillState.DISABLED
        skill.metadata.state = SkillState.DISABLED
        del self._skills[skill_name]
        if skill_name in self._manifests:
            del self._manifests[skill_name]

        logger.info(f"Skill '{skill_name}' unregistered.")
        return True

    def get_skill(self, skill_name: str) -> Optional[BaseSkill]:
        return self._skills.get(skill_name)

    def get_manifest(self, skill_name: str) -> Optional[SkillManifest]:
        return self._manifests.get(skill_name)

    def list_skills(self) -> List[SkillMetadata]:
        return [s.metadata for s in self._skills.values()]

    def list_active_skills(self) -> List[BaseSkill]:
        return [s for s in self._skills.values() if s.state == SkillState.ACTIVE]

    def find_action(self, action_name: str) -> Optional[Tuple[BaseSkill, ActionSchema]]:
        """Finds skill and schema providing a specific action name."""
        if action_name in self._actions:
            skill_name, schema = self._actions[action_name]
            skill = self.get_skill(skill_name)
            if skill:
                return (skill, schema)
        return None

    def find_skills_by_query(self, query: str) -> List[BaseSkill]:
        """Finds matching skills based on keywords, name, description, and action verbs."""
        q_lower = query.lower()
        matched: List[BaseSkill] = []

        for skill in self._skills.values():
            m = skill.manifest
            if q_lower in m.name.lower() or (m.display_name and q_lower in m.display_name.lower()):
                matched.append(skill)
                continue
            if any(q_lower in tag.lower() for tag in m.tags):
                matched.append(skill)
                continue
            if q_lower in m.description.lower():
                matched.append(skill)
                continue
            if any(q_lower in a.name.lower() or q_lower in a.description.lower() for a in m.actions):
                matched.append(skill)
                continue

        return matched

    async def get_health_status(self) -> Dict[str, SkillHealth]:
        """Collects health status of all registered skills."""
        report: Dict[str, SkillHealth] = {}
        for name, skill in self._skills.items():
            report[name] = await skill.health()
        return report
