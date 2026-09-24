"""
SHIVANI Browser Content Tools
Registered tools for text extraction, web summarization, structured data scraping,
screenshots, file uploads/downloads, and media operations.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.browser.agent import BrowserAgent


class BrowserExtractTextArgs(BaseModel):
    selector: Optional[str] = Field(default=None, description="Optional CSS/XPath selector to restrict text extraction")


class BrowserExtractTextTool(BaseTool):
    name = "browser.extract_text"
    description = "Extract readable text content from the current webpage or specific element."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserExtractTextArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, selector: Optional[str] = None) -> Dict[str, Any]:
        text = await self.browser_agent.extract_text(selector=selector)
        return {"text": text, "length": len(text)}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("text"))}


class BrowserExtractLinksArgs(BaseModel):
    selector: Optional[str] = Field(default=None, description="Optional CSS selector to scope link search")


class BrowserExtractLinksTool(BaseTool):
    name = "browser.extract_links"
    description = "Extract hyperlinks with text and URLs from the active webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserExtractLinksArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, selector: Optional[str] = None) -> Dict[str, Any]:
        links = await self.browser_agent.extract_links(selector=selector)
        return {"links": links, "count": len(links)}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class BrowserSummarizeTool(BaseTool):
    name = "browser.summarize"
    description = "Extract and intelligently summarize main content and sections of the active webpage."
    permission_level = RiskLevel.SAFE
    timeout = 30.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        return await self.browser_agent.summarize_page()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("summary"))}


class BrowserExtractDataArgs(BaseModel):
    extraction_type: str = Field(default="general", description="Extraction mode: 'general', 'articles', 'products', 'links', 'headings'")


class BrowserExtractDataTool(BaseTool):
    name = "browser.extract_data"
    description = "Extract structured data, headings, articles, or listings from the webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserExtractDataArgs
    timeout = 25.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, extraction_type: str = "general") -> Dict[str, Any]:
        return await self.browser_agent.extract_page_data(extraction_type=extraction_type)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success"}


class BrowserScreenshotArgs(BaseModel):
    output_path: Optional[str] = Field(default=None, description="Target filesystem path for saved image (.png)")
    full_page: bool = Field(default=False, description="Whether to capture full scrollable page")


class BrowserScreenshotTool(BaseTool):
    name = "browser.screenshot"
    description = "Capture a screenshot of the active browser webpage."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserScreenshotArgs
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, output_path: Optional[str] = None, full_page: bool = False) -> Dict[str, Any]:
        save_path = Path(output_path) if output_path else Path("screenshots") / f"browser_{Path('.').stat().st_mtime_ns}.png"
        return await self.browser_agent.capture_screenshot(output_path=save_path, full_page=full_page)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        p = Path(result_data.get("path", ""))
        return {"verified": p.exists() and p.stat().st_size > 0, "path": str(p)}


class BrowserUploadFileArgs(BaseModel):
    target: str = Field(description="File input element selector or description")
    file_path: str = Field(description="Local file path to upload")


class BrowserUploadFileTool(BaseTool):
    name = "browser.upload_file"
    description = "Upload a local file into a web form file input field."
    permission_level = RiskLevel.SENSITIVE
    args_schema = BrowserUploadFileArgs
    timeout = 20.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, target: str, file_path: str) -> Dict[str, Any]:
        return await self.browser_agent.upload_file(target=target, file_path=file_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "file": kwargs.get("file_path")}


class BrowserDownloadFileArgs(BaseModel):
    trigger_target: str = Field(description="Button or link element to click to trigger download")
    destination_dir: Optional[str] = Field(default=None, description="Directory where file will be saved")


class BrowserDownloadFileTool(BaseTool):
    name = "browser.download_file"
    description = "Click an element to trigger a file download and save it to disk."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserDownloadFileArgs
    timeout = 35.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, trigger_target: str, destination_dir: Optional[str] = None) -> Dict[str, Any]:
        dest_path = Path(destination_dir) if destination_dir else None
        return await self.browser_agent.download_file(trigger_target=trigger_target, destination_dir=dest_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        p = Path(result_data.get("destination_path", ""))
        return {"verified": p.exists() and p.stat().st_size > 0, "path": str(p)}


class BrowserPlayYouTubeArgs(BaseModel):
    query: str = Field(description="Song title, artist, or video query to search and play on YouTube")


class BrowserPlayYouTubeTool(BaseTool):
    name = "browser.play_youtube"
    description = "Search YouTube for a song or video, select the best matching result, and verify playback."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserPlayYouTubeArgs
    timeout = 40.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, query: str) -> Dict[str, Any]:
        return await self.browser_agent.play_youtube(query=query)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        playback = result_data.get("playback_verified", False)
        return {
            "verified": playback,
            "video_title": result_data.get("video_title"),
            "playback_verified": playback
        }
