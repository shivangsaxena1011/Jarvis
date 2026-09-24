"""
SHIVANI Skill Runtime Base
Defines the BaseSkill abstract base class that all SHIVANI dynamic skills implement.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional

from tools.base import BaseTool
from skills.manifest import SkillManifest
from skills.models import ActionSchema, SkillHealth, SkillMetadata, SkillState
from skills.sandbox import SkillSandbox


class BaseSkill(ABC):
    """Abstract base class for extensible capabilities and skills."""

    def __init__(
        self,
        manifest: SkillManifest,
        sandbox: Optional[SkillSandbox] = None,
    ):
        self.manifest = manifest
        self.sandbox = sandbox or SkillSandbox(manifest)
        self.state: SkillState = SkillState.INSTALLED
        self.logger = logging.getLogger(f"shivani.skills.{manifest.name}")
        self.metadata = SkillMetadata(
            name=manifest.name,
            version=manifest.version,
            display_name=manifest.display_name or manifest.name,
            description=manifest.description,
            author=manifest.author,
            state=self.state,
        )

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def version(self) -> str:
        return self.manifest.version

    @abstractmethod
    async def initialize(self) -> None:
        """Initializes skill resources, network connections, or background workers."""
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """Gracefully releases resources and workers."""
        pass

    async def health(self) -> SkillHealth:
        """Returns the current operational health of the skill."""
        if self.state == SkillState.FAILED:
            return SkillHealth.UNHEALTHY
        if self.state == SkillState.DEGRADED:
            return SkillHealth.DEGRADED
        if self.sandbox.telemetry.errors > 0:
            if self.sandbox.telemetry.invocations > 0:
                err_rate = self.sandbox.telemetry.errors / self.sandbox.telemetry.invocations
                if err_rate > 0.5:
                    return SkillHealth.UNHEALTHY
                elif err_rate > 0.1:
                    return SkillHealth.DEGRADED
        return SkillHealth.HEALTHY

    def capabilities(self) -> List[ActionSchema]:
        """Returns schemas for the verbs/actions exposed by this skill."""
        return self.manifest.actions

    def get_tools(self) -> List[BaseTool]:
        """Returns instantiated BaseTool objects to register with ToolRegistry."""
        return []

    def get_agents(self) -> List[Any]:
        """Returns any subagents provided by this skill."""
        return []

    async def execute_action(self, action_name: str, **kwargs: Any) -> Any:
        """Executes a named action within the skill's sandbox."""
        raise NotImplementedError(f"Action '{action_name}' not implemented by {self.name}")
