"""
SHIVANI Gmail Registered Tools
Registered tools for Gmail inbox inspection, categorized summaries, and two-stage cleanup.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from integrations.gmail.service import GmailService
from agents.browser.agent import BrowserAgent


class GmailOpenTool(BaseTool):
    name = "gmail.open"
    description = "Open and navigate to Gmail inbox."
    permission_level = RiskLevel.SAFE
    timeout = 30.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.open_gmail()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("url"))}


class GmailListUnreadArgs(BaseModel):
    limit: int = Field(default=20, description="Maximum number of unread emails to retrieve")


class GmailListUnreadTool(BaseTool):
    name = "gmail.list_unread"
    description = "List recent unread emails with sender, subject, and snippet preview."
    permission_level = RiskLevel.SAFE
    args_schema = GmailListUnreadArgs
    timeout = 30.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self, limit: int = 20) -> Dict[str, Any]:
        items = await self.service.list_unread(limit=limit)
        return {"count": len(items), "messages": items}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class GmailSearchArgs(BaseModel):
    query: str = Field(description="Search terms for finding emails in Gmail")


class GmailSearchTool(BaseTool):
    name = "gmail.search"
    description = "Search emails in Gmail by keyword, sender, or subject."
    permission_level = RiskLevel.SAFE
    args_schema = GmailSearchArgs
    timeout = 30.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self, query: str) -> Dict[str, Any]:
        msgs = await self.service.search(query=query)
        return {"query": query, "count": len(msgs), "messages": msgs}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class GmailSummarizeTool(BaseTool):
    name = "gmail.summarize"
    description = "Categorize unread emails (important, personal, work, promotional, spam) and generate summary."
    permission_level = RiskLevel.SAFE
    timeout = 35.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.summarize_inbox()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("summary_text")), "total": result_data.get("total_unread", 0)}


class GmailCleanupProposalTool(BaseTool):
    name = "gmail.cleanup_proposal"
    description = "Analyze inbox and generate cleanup proposal classifying promotional/newsletter emails for archive."
    permission_level = RiskLevel.SAFE
    timeout = 30.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.generate_cleanup_proposal()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("proposal_id"))}


class GmailExecuteCleanupArgs(BaseModel):
    proposal_id: str = Field(description="Unique cleanup proposal ID approved by user")
    action: str = Field(default="archive", description="Action to perform: 'archive' or 'mark_read'")


class GmailExecuteCleanupTool(BaseTool):
    name = "gmail.execute_cleanup"
    description = "Execute an approved email cleanup batch (Requires User Approval)."
    permission_level = RiskLevel.SENSITIVE
    args_schema = GmailExecuteCleanupArgs
    requires_confirmation = True
    timeout = 35.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self, proposal_id: str, action: str = "archive") -> Dict[str, Any]:
        return await self.service.execute_cleanup(proposal_id=proposal_id, action=action)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False), "count": result_data.get("count_processed", 0)}


class GmailDeleteArgs(BaseModel):
    message_id: str = Field(description="Message ID to delete")


class GmailDeleteTool(BaseTool):
    name = "gmail.delete"
    description = "Delete a specific email message permanently (Requires CRITICAL Approval)."
    permission_level = RiskLevel.CRITICAL
    args_schema = GmailDeleteArgs
    requires_confirmation = True
    timeout = 15.0

    def __init__(self, gmail_service: Optional[GmailService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = gmail_service or GmailService(browser_agent or BrowserAgent())

    async def run(self, message_id: str) -> Dict[str, Any]:
        return await self.service.delete(message_id)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False)}
