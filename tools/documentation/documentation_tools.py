"""
SHIVANI Documentation Registered Tools
Registered tools for generating READMEs, OpenAPI specs, and Architecture Decision Records (ADRs).
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.documentation.agent import DocumentationAgent


class DocumentationGenerateReadmeArgs(BaseModel):
    project_path: str = Field(description="Local path to software project directory")


class DocumentationGenerateReadmeTool(BaseTool):
    name = "documentation.generate_readme"
    description = "Inspect project directory and generate production-grade README.md."
    permission_level = RiskLevel.SAFE
    args_schema = DocumentationGenerateReadmeArgs
    timeout = 25.0

    def __init__(self, doc_agent: Optional[DocumentationAgent] = None):
        super().__init__()
        self.agent = doc_agent or DocumentationAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        return self.agent.generate_readme(project_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("readme_text"))}


class DocumentationGenerateApiDocsArgs(BaseModel):
    project_path: str = Field(description="Local path to software project directory")


class DocumentationGenerateApiDocsTool(BaseTool):
    name = "documentation.generate_api_docs"
    description = "Inspect project routes and controllers to generate OpenAPI / API documentation."
    permission_level = RiskLevel.SAFE
    args_schema = DocumentationGenerateApiDocsArgs
    timeout = 25.0

    def __init__(self, doc_agent: Optional[DocumentationAgent] = None):
        super().__init__()
        self.agent = doc_agent or DocumentationAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        return self.agent.generate_api_docs(project_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("endpoints_count", 0) > 0}


class DocumentationGenerateArchDocArgs(BaseModel):
    project_path: str = Field(description="Local path to software project directory")


class DocumentationGenerateArchDocTool(BaseTool):
    name = "documentation.generate_architecture_doc"
    description = "Generate Architecture Decision Record (ADR) and component boundary documentation."
    permission_level = RiskLevel.SAFE
    args_schema = DocumentationGenerateArchDocArgs
    timeout = 25.0

    def __init__(self, doc_agent: Optional[DocumentationAgent] = None):
        super().__init__()
        self.agent = doc_agent or DocumentationAgent()

    async def run(self, project_path: str) -> Dict[str, Any]:
        return self.agent.generate_architecture_doc(project_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("architecture_text"))}
