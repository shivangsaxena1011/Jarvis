"""
SHIVANI Browser Tab Tools
Registered tools for managing multi-tab operations: opening, switching, closing, and listing tabs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from agents.browser.agent import BrowserAgent


class BrowserNewTabArgs(BaseModel):
    url: str = Field(default="about:blank", description="Initial URL for new tab")


class BrowserNewTabTool(BaseTool):
    name = "browser.new_tab"
    description = "Open a new browser tab with optional URL."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserNewTabArgs
    timeout = 20.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, url: str = "about:blank") -> Dict[str, Any]:
        page = await self.browser_agent.new_tab(url=url)
        return {"status": "tab_opened", "url": page.url, "title": await page.title()}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "tab_opened"}


class BrowserSwitchTabArgs(BaseModel):
    tab_id: str = Field(description="Tab identifier or title/index to switch to")


class BrowserSwitchTabTool(BaseTool):
    name = "browser.switch_tab"
    description = "Switch active focus to a different browser tab by ID or index."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserSwitchTabArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, tab_id: str) -> Dict[str, Any]:
        page = await self.browser_agent.switch_tab(tab_id)
        if page:
            return {"status": "switched", "tab_id": tab_id, "url": page.url, "title": await page.title()}
        return {"status": "not_found", "tab_id": tab_id}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "switched"}


class BrowserCloseTabArgs(BaseModel):
    tab_id: Optional[str] = Field(default=None, description="Tab identifier to close, or None for current tab")


class BrowserCloseTabTool(BaseTool):
    name = "browser.close_tab"
    description = "Close a specific browser tab or the active tab."
    permission_level = RiskLevel.SAFE
    args_schema = BrowserCloseTabArgs
    timeout = 10.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self, tab_id: Optional[str] = None) -> Dict[str, Any]:
        closed = await self.browser_agent.close_tab(tab_id)
        return {"status": "closed" if closed else "failed", "tab_id": tab_id}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "closed"}


class BrowserListTabsTool(BaseTool):
    name = "browser.list_tabs"
    description = "List all currently open browser tabs and their URLs."
    permission_level = RiskLevel.SAFE
    timeout = 5.0

    def __init__(self, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.browser_agent = browser_agent or BrowserAgent()

    async def run(self) -> Dict[str, Any]:
        tabs = await self.browser_agent.list_tabs()
        return {"count": len(tabs), "tabs": tabs}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}
