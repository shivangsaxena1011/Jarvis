"""
SHIVANI Extensibility Tools
Agent tools for inspecting, listing, enabling, and managing Universal Skills,
App Connectors, and Multi-surface Adapters.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from security.permissions.models import RiskLevel
from tools.base import BaseTool, ToolResult
from skills.registry import SkillRegistry
from skills.lifecycle import SkillLifecycleManager
from connectors.registry import ConnectorRegistry
from adapters.registry import AdapterRegistry


class SkillListArgs(BaseModel):
    query: Optional[str] = Field(default=None, description="Optional search term to filter skills")


class SkillListTool(BaseTool):
    name = "skill_list"
    description = "Lists all installed and active universal skills with their capabilities and status."
    permission_level = RiskLevel.SAFE
    args_schema = SkillListArgs

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry

    async def run(self, query: Optional[str] = None, **kwargs: Any) -> ToolResult:
        if not self.registry:
            return ToolResult(success=False, error="Skill registry not configured.")

        if query:
            skills = self.registry.find_skills_by_query(query)
            data = [s.metadata.model_dump() for s in skills]
        else:
            data = [m.model_dump() for m in self.registry.list_skills()]

        return ToolResult(success=True, data={"skills": data, "count": len(data)})


class SkillInfoArgs(BaseModel):
    skill_name: str = Field(..., description="Name slug of the skill to inspect")


class SkillInfoTool(BaseTool):
    name = "skill_info"
    description = "Retrieves full manifest, permissions, and exposed action schemas for a skill."
    permission_level = RiskLevel.SAFE
    args_schema = SkillInfoArgs

    def __init__(self, registry: Optional[SkillRegistry] = None):
        self.registry = registry

    async def run(self, skill_name: str, **kwargs: Any) -> ToolResult:
        if not self.registry:
            return ToolResult(success=False, error="Skill registry not configured.")

        manifest = self.registry.get_manifest(skill_name)
        if not manifest:
            return ToolResult(success=False, error=f"Skill '{skill_name}' not found.")

        return ToolResult(success=True, data=manifest.model_dump())


class ConnectorListTool(BaseTool):
    name = "connector_list"
    description = "Lists all third-party app connectors, active accounts, and connection statuses."
    permission_level = RiskLevel.SAFE

    def __init__(self, registry: Optional[ConnectorRegistry] = None):
        self.registry = registry

    async def run(self, **kwargs: Any) -> ToolResult:
        if not self.registry:
            return ToolResult(success=False, error="Connector registry not configured.")

        connectors = self.registry.list_connectors()
        return ToolResult(success=True, data={"connectors": connectors, "count": len(connectors)})


class AdapterListArgs(BaseModel):
    app_type: Optional[str] = Field(default=None, description="Filter by 'desktop', 'browser', or 'mobile'")


class AdapterListTool(BaseTool):
    name = "adapter_list"
    description = "Lists available applications and execution adapters across desktop, browser, and mobile surfaces."
    permission_level = RiskLevel.SAFE
    args_schema = AdapterListArgs

    def __init__(self, registry: Optional[AdapterRegistry] = None):
        self.registry = registry

    async def run(self, app_type: Optional[str] = None, **kwargs: Any) -> ToolResult:
        if not self.registry:
            return ToolResult(success=False, error="Adapter registry not configured.")

        adapters = self.registry.list_adapters(app_type=app_type)
        data = [{"name": a.name, "type": a.app_type} for a in adapters]
        return ToolResult(success=True, data={"adapters": data, "count": len(data)})
