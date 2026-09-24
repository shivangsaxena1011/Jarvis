"""
SHIVANI Knowledge OS Tools
Exposes workspace knowledge retrieval, project context inspection,
indexing, graph querying, and note creation as callable tools.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from knowledge.service import KnowledgeOS, get_knowledge_os
from security.permissions.engine import RiskLevel
from tools.base import BaseTool


class KnowledgeSearchArgs(BaseModel):
    query: str = Field(..., description="Search query string to search workspace knowledge for")
    project_id: Optional[str] = Field(default=None, description="Optional project ID to filter results")
    limit: int = Field(default=5, description="Maximum number of results to retrieve")


class KnowledgeSearchTool(BaseTool):
    name = "knowledge.search"
    description = "Searches the unified knowledge base across documents, code, research, and notes using hybrid RAG."
    permission_level = RiskLevel.SAFE
    args_schema = KnowledgeSearchArgs

    def __init__(self, knowledge_os: Optional[KnowledgeOS] = None):
        self.knowledge_os = knowledge_os or get_knowledge_os()

    async def run(self, query: str, project_id: Optional[str] = None, limit: int = 5) -> Dict[str, Any]:
        return self.knowledge_os.search(query=query, project_id=project_id, limit=limit)


class KnowledgeGetProjectContextArgs(BaseModel):
    project_id_or_path: str = Field(..., description="Project ID or root directory path")


class KnowledgeGetProjectContextTool(BaseTool):
    name = "knowledge.get_project_context"
    description = "Retrieves structured architectural blueprints, tech stack, and dependencies for a project."
    permission_level = RiskLevel.SAFE
    args_schema = KnowledgeGetProjectContextArgs

    def __init__(self, knowledge_os: Optional[KnowledgeOS] = None):
        self.knowledge_os = knowledge_os or get_knowledge_os()

    async def run(self, project_id_or_path: str) -> Dict[str, Any]:
        context_md = self.knowledge_os.get_project_context(project_id_or_path)
        return {"project_context": context_md}


class KnowledgeIndexPathArgs(BaseModel):
    path: str = Field(..., description="File path or directory path to index into Knowledge OS")
    project_id: Optional[str] = Field(default=None, description="Optional project ID association")


class KnowledgeIndexPathTool(BaseTool):
    name = "knowledge.index_path"
    description = "Indexes a document, code file, or entire project directory into the Knowledge OS."
    permission_level = RiskLevel.SAFE
    args_schema = KnowledgeIndexPathArgs

    def __init__(self, knowledge_os: Optional[KnowledgeOS] = None):
        self.knowledge_os = knowledge_os or get_knowledge_os()

    async def run(self, path: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        import os
        if os.path.isdir(path):
            res = self.knowledge_os.index_directory(path, project_id=project_id)
            return {"success": True, "details": res}
        elif os.path.isfile(path):
            item = self.knowledge_os.index_file(path, project_id=project_id)
            return {
                "success": item is not None,
                "item_id": item.id if item else None,
                "chunks_count": len(item.chunks) if item else 0,
            }
        else:
            return {"success": False, "error": f"Path not found: {path}"}


class KnowledgeQueryGraphArgs(BaseModel):
    start_node: str = Field(..., description="Node ID to start graph exploration from")
    max_depth: int = Field(default=2, description="Exploration radius depth (hops)")


class KnowledgeQueryGraphTool(BaseTool):
    name = "knowledge.query_graph"
    description = "Explores the knowledge graph to discover relationships, callers, and dependencies."
    permission_level = RiskLevel.SAFE
    args_schema = KnowledgeQueryGraphArgs

    def __init__(self, knowledge_os: Optional[KnowledgeOS] = None):
        self.knowledge_os = knowledge_os or get_knowledge_os()

    async def run(self, start_node: str, max_depth: int = 2) -> Dict[str, Any]:
        return self.knowledge_os.query_graph(start_node=start_node, max_depth=max_depth)


class KnowledgeAddNoteArgs(BaseModel):
    title: str = Field(..., description="Title of the note or decision")
    content: str = Field(..., description="Content of the note or decision")
    project_id: Optional[str] = Field(default=None, description="Optional project ID association")
    is_decision: bool = Field(default=False, description="Set True if this records an architectural decision")


class KnowledgeAddNoteTool(BaseTool):
    name = "knowledge.add_note"
    description = "Records a personal note or architectural decision into persistent knowledge memory."
    permission_level = RiskLevel.SAFE
    args_schema = KnowledgeAddNoteArgs

    def __init__(self, knowledge_os: Optional[KnowledgeOS] = None):
        self.knowledge_os = knowledge_os or get_knowledge_os()

    async def run(
        self,
        title: str,
        content: str,
        project_id: Optional[str] = None,
        is_decision: bool = False,
    ) -> Dict[str, Any]:
        item = self.knowledge_os.add_note(
            title=title,
            content=content,
            project_id=project_id,
            is_decision=is_decision,
        )
        return {"success": True, "note_id": item.id, "title": item.title}
