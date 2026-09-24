"""
SHIVANI LinkedIn Registered Tools
Registered tools for LinkedIn feed inspection, professional draft preparation, and safe publishing.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from integrations.linkedin.service import LinkedInService
from agents.browser.agent import BrowserAgent


class LinkedInOpenTool(BaseTool):
    name = "linkedin.open"
    description = "Open and navigate to LinkedIn feed."
    permission_level = RiskLevel.SAFE
    timeout = 30.0

    def __init__(self, linkedin_service: Optional[LinkedInService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = linkedin_service or LinkedInService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        return await self.service.open_linkedin()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": bool(result_data.get("url"))}


class LinkedInReadFeedTool(BaseTool):
    name = "linkedin.read_feed"
    description = "Read visible posts from active LinkedIn feed."
    permission_level = RiskLevel.SAFE
    timeout = 25.0

    def __init__(self, linkedin_service: Optional[LinkedInService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = linkedin_service or LinkedInService(browser_agent or BrowserAgent())

    async def run(self) -> Dict[str, Any]:
        posts = await self.service.read_visible_feed()
        return {"count": len(posts), "posts": posts}

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": True, "count": result_data.get("count", 0)}


class LinkedInPreparePostArgs(BaseModel):
    post_text: str = Field(description="Full text content for the LinkedIn post draft")
    image_path: Optional[str] = Field(default=None, description="Optional path to local image file to attach")


class LinkedInPreparePostTool(BaseTool):
    name = "linkedin.prepare_post"
    description = "Prepare a professional LinkedIn post in DRAFT mode (Does NOT publish)."
    permission_level = RiskLevel.SAFE
    args_schema = LinkedInPreparePostArgs
    timeout = 15.0

    def __init__(self, linkedin_service: Optional[LinkedInService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = linkedin_service or LinkedInService(browser_agent or BrowserAgent())

    async def run(self, post_text: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        return await self.service.prepare_post(post_text=post_text, image_path=image_path)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "DRAFT" and bool(result_data.get("draft_id"))}


class LinkedInPrepareCommentArgs(BaseModel):
    post_context: str = Field(description="Context or snippet of post being replied to")
    comment_text: str = Field(description="Comment body to draft")


class LinkedInPrepareCommentTool(BaseTool):
    name = "linkedin.prepare_comment"
    description = "Draft a professional comment for a LinkedIn post (Requires Approval before posting)."
    permission_level = RiskLevel.SENSITIVE
    args_schema = LinkedInPrepareCommentArgs
    requires_confirmation = True
    timeout = 15.0

    def __init__(self, linkedin_service: Optional[LinkedInService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = linkedin_service or LinkedInService(browser_agent or BrowserAgent())

    async def run(self, post_context: str, comment_text: str) -> Dict[str, Any]:
        return await self.service.prepare_comment(post_context=post_context, comment_text=comment_text)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("status") == "DRAFT"}


class LinkedInPublishPostArgs(BaseModel):
    draft_id: str = Field(description="Approved draft ID to publish to LinkedIn feed")


class LinkedInPublishPostTool(BaseTool):
    name = "linkedin.publish_post"
    description = "Publish an approved post draft to LinkedIn (Strictly Requires CRITICAL Confirmation)."
    permission_level = RiskLevel.CRITICAL
    args_schema = LinkedInPublishPostArgs
    requires_confirmation = True
    timeout = 40.0

    def __init__(self, linkedin_service: Optional[LinkedInService] = None, browser_agent: Optional[BrowserAgent] = None):
        super().__init__()
        self.service = linkedin_service or LinkedInService(browser_agent or BrowserAgent())

    async def run(self, draft_id: str) -> Dict[str, Any]:
        return await self.service.publish_post(draft_id=draft_id)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("verified", False) and result_data.get("status") == "PUBLISHED"}
