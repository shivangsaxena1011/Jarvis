"""
SHIVANI Browser Navigation Tools
Registered tools for launching, navigating, searching, and managing browser lifecycle.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.browser.agent import BrowserAgent


class BrowserOpenArgs(BaseModel):
    url: str = Field(default="https://www.google.com", description="Initial URL to open in browser")


class BrowserOpenTool(BaseTool):
    name = "browser.open"
    description = "Launch the web browser and navigate to the specified URL."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserOpenArgs
    timeout = 30.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, url: str = "https://www.google.com") -> Dict[str, Any]:
        return await self.browser_agent.navigate(url)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        url = result_data.get("url", "")
        verified = bool(url and not url.startswith("about:blank"))
        return {"verified": verified, "url": url, "title": result_data.get("title", "")}


class BrowserCloseTool(BaseTool):
    name = "browser.close"
    description = "Close the browser session and clean up open windows."
    permission_level = RiskLevel.SAFE
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        await self.browser_agent.close()
        return {"status": "closed", "success": True}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class BrowserNavigateArgs(BaseModel):
    url: str = Field(description="URL to navigate to (e.g. 'https://youtube.com', 'google.com')")


class BrowserNavigateTool(BaseTool):
    name = "browser.navigate"
    description = "Navigate the active browser tab to a specific web address."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserNavigateArgs
    timeout = 30.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, url: str) -> Dict[str, Any]:
        return await self.browser_agent.navigate(url)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        verified = result_data.get("verified", False)
        return {"verified": verified, "current_url": result_data.get("url")}


class BrowserBackTool(BaseTool):
    name = "browser.back"
    description = "Navigate back to the previous page in history."
    permission_level = RiskLevel.SAFE
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        return await self.browser_agent.go_back()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "url": result_data.get("url")}


class BrowserForwardTool(BaseTool):
    name = "browser.forward"
    description = "Navigate forward to the next page in history."
    permission_level = RiskLevel.SAFE
    timeout = 15.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        return await self.browser_agent.go_forward()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "url": result_data.get("url")}


class BrowserRefreshTool(BaseTool):
    name = "browser.refresh"
    description = "Reload the current webpage."
    permission_level = RiskLevel.SAFE
    timeout = 20.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        return await self.browser_agent.refresh()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "success", "url": result_data.get("url")}


class BrowserGetTitleTool(BaseTool):
    name = "browser.get_title"
    description = "Get the title of the currently active webpage."
    permission_level = RiskLevel.SAFE
    timeout = 5.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, str]:
        title = await self.browser_agent.get_title()
        return {"title": title}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "title": result_data.get("title")}


class BrowserGetUrlTool(BaseTool):
    name = "browser.get_url"
    description = "Get the URL of the currently active webpage."
    permission_level = RiskLevel.SAFE
    timeout = 5.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, str]:
        url = await self.browser_agent.get_url()
        return {"url": url}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "url": result_data.get("url")}


class BrowserSearchArgs(BaseModel):
    query: str = Field(description="Search terms or query string")
    engine: str = Field(default="google", description="Search engine to use: 'google', 'bing', or 'duckduckgo'")


class BrowserSearchTool(BaseTool):
    name = "browser.search"
    description = "Search the web using a search engine like Google or Bing."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserSearchArgs
    timeout = 30.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, query: str, engine: str = "google") -> Dict[str, Any]:
        return await self.browser_agent.search(query=query, engine=engine)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        verified = result_data.get("verified", False)
        return {"verified": verified, "query": kwargs.get("query"), "results_count": result_data.get("results_count", 0)}
