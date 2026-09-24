"""
SHIVANI Project Context Registered Tools
Registered tools for locating, inspecting, and listing local software projects.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from core.projects.indexer import ProjectIndexer


class ProjectFindArgs(BaseModel):
    query: str = Field(description="Project name or keywords (e.g. 'Heart Disease', 'ET Hackathon')")


class ProjectFindTool(BaseTool):
    name = "project.find"
    description = "Locate and inspect a software project from authorized local project roots."
    permission_level = RiskLevel.SAFE
    args_schema = ProjectFindArgs
    timeout = 15.0

    def __init__(self, indexer: Optional[ProjectIndexer] = None):
        super().__init__()
        self.indexer = indexer or ProjectIndexer()

    async def run(self, query: str) -> Dict[str, Any]:
        meta = self.indexer.find_project(query)
        if meta:
            return meta.model_dump()
        return {"status": "not_found", "query": query}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("path")), "name": result_data.get("name")}


class ProjectListTool(BaseTool):
    name = "project.list"
    description = "List all detected local software projects in authorized roots."
    permission_level = RiskLevel.SAFE
    timeout = 15.0

    def __init__(self, indexer: Optional[ProjectIndexer] = None):
        super().__init__()
        self.indexer = indexer or ProjectIndexer()

    async def run(self) -> Dict[str, Any]:
        projs = self.indexer.list_projects()
        return {"count": len(projs), "projects": [p.model_dump() for p in projs]}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}
