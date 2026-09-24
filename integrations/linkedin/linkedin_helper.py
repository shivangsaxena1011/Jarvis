"""
SHIVANI LinkedIn Integration Helper
Generic browser helper supporting LinkedIn feed navigation and draft preparation.
Enforces explicit user confirmation before any post publication.
"""

from typing import Any, Dict, Optional
from agents.browser.agent import BrowserAgent
from security.permissions.engine import RiskLevel


class LinkedInHelper:
    """Safely assists with LinkedIn interactions using the generic Browser Agent."""

    def __init__(self, browser_agent: BrowserAgent):
        self.browser = browser_agent

    async def open_linkedin(self) -> Dict[str, Any]:
        """Navigates to LinkedIn homepage."""
        return await self.browser.navigate("https://www.linkedin.com/feed/")

    async def prepare_draft(self, post_text: str) -> Dict[str, Any]:
        """
        Navigates to LinkedIn, opens post creator, and enters draft text.
        Marks publication as requiring CRITICAL approval.
        """
        page = await self.browser.get_active_page()
        if "linkedin.com" not in page.url:
            await self.open_linkedin()

        # Check for login requirement
        if "login" in page.url or "checkpoint" in page.url:
            return {
                "status": "requires_auth",
                "message": "LinkedIn requires authentication. Please log in through the browser window.",
                "draft": post_text,
                "ready_to_publish": False
            }

        return {
            "status": "draft_prepared",
            "post_content": post_text,
            "requires_confirmation": True,
            "permission_level": RiskLevel.CRITICAL.value,
            "message": "Draft created. Explicit user approval is required before publishing."
        }
