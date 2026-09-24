"""
SHIVANI Research Registered Tools
Registered tools for web and academic research, citation tracking, and report generation.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from integrations.research.service import ResearchService
from agents.browser.agent import BrowserAgent


class ResearchSearchArgs(BaseModel):
    query: str = Field(description="Research query or topic keywords")
    limit: int = Field(default=5, description="Maximum number of sources to collect")


class ResearchSearchTool(BaseTool):
    name = "research.search"
    description = "Search web and academic sources with citation and relevance tracking."
    permission_level = RiskLevel.SAFE
    args_schema = ResearchSearchArgs
    timeout = 30.0

    def __init__(self, research_service: Optional[ResearchService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = research_service or ResearchService(browser_agent)

    async def run(self, query: str, limit: int = 5) -> Dict[str, Any]:
        return await self.service.search(query=query, limit=limit)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("count", 0) > 0, "sources_count": result_data.get("count", 0)}


class ResearchOpenSourceArgs(BaseModel):
    url: str = Field(description="URL of source paper or article to read")


class ResearchOpenSourceTool(BaseTool):
    name = "research.open_source"
    description = "Navigate to a research source and extract full textual content."
    permission_level = RiskLevel.SAFE
    args_schema = ResearchOpenSourceArgs
    timeout = 30.0

    def __init__(self, research_service: Optional[ResearchService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = research_service or ResearchService(browser_agent)

    async def run(self, url: str) -> Dict[str, Any]:
        return await self.service.open_source(url)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("chars_extracted", 0) > 0}


class ResearchSummarizeArgs(BaseModel):
    query: Optional[str] = Field(default=None, description="Research topic being synthesized")
    topic: Optional[str] = Field(default=None, description="Alternative topic alias")
    sources: Optional[List[Dict[str, Any]]] = Field(default=None, description="Optional list of cited sources")


class ResearchSummarizeTool(BaseTool):
    name = "research.summarize"
    description = "Synthesize key takeaways and comparative analysis from collected research sources."
    permission_level = RiskLevel.SAFE
    args_schema = ResearchSummarizeArgs
    timeout = 25.0

    def __init__(self, research_service: Optional[ResearchService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = research_service or ResearchService(browser_agent)

    async def run(
        self,
        query: Optional[str] = None,
        topic: Optional[str] = None,
        sources: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        target_query = query or topic or "General Research"
        srcs = sources
        if not srcs:
            search_res = await self.service.search(query=target_query, limit=5)
            srcs = search_res.get("sources", [])
        summary = self.service.summarize_sources(query=target_query, sources=srcs)
        return {"query": target_query, "summary": summary, "sources": srcs}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("summary"))}


class ResearchSaveReportArgs(BaseModel):
    query: Optional[str] = Field(default=None, description="Research topic title")
    topic: Optional[str] = Field(default=None, description="Alternative topic alias")
    summary: Optional[str] = Field(default=None, description="Executive summary content")
    output_dir: Optional[str] = Field(default=None, description="Optional custom directory path")


class ResearchSaveReportTool(BaseTool):
    name = "research.save"
    description = "Save research bundle (report.md, sources.json, summary.json) to disk."
    permission_level = RiskLevel.SAFE
    args_schema = ResearchSaveReportArgs
    timeout = 20.0

    def __init__(self, research_service: Optional[ResearchService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = research_service or ResearchService(browser_agent)

    async def run(
        self,
        query: Optional[str] = None,
        topic: Optional[str] = None,
        summary: Optional[str] = None,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_query = query or topic or "General Research"
        search_res = await self.service.search(query=target_query, limit=5)
        srcs = search_res.get("sources", [])
        summ = summary or self.service.summarize_sources(query=target_query, sources=srcs)
        return await self.service.save_report(query=target_query, summary=summ, sources=srcs, output_dir=output_dir)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        from pathlib import Path
        rep = Path(result_data.get("report_path", ""))
        return {"verified": rep.exists() and rep.stat().st_size > 0, "path": str(rep)}
