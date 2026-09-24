"""
SHIVANI Gmail Integration Helper
Generic browser helper supporting Gmail inbox navigation, message reading,
summarizing unread emails, and search. Destructive actions require confirmation.
"""

from typing import Any, Dict, List, Optional
from agents.browser.agent import BrowserAgent
from security.permissions.engine import RiskLevel


class GmailHelper:
    """Safely assists with Gmail interactions through the generic Browser Agent."""

    def __init__(self, browser_agent: BrowserAgent):
        self.browser = browser_agent

    async def open_gmail(self) -> Dict[str, Any]:
        """Navigates to Gmail inbox."""
        return await self.browser.navigate("https://mail.google.com")

    async def inspect_inbox(self) -> Dict[str, Any]:
        """Inspects inbox state and detects unread email threads."""
        page = await self.browser.get_active_page()
        if "mail.google.com" not in page.url:
            await self.open_gmail()

        if "accounts.google.com" in page.url or "signin" in page.url:
            return {
                "status": "requires_auth",
                "message": "Gmail requires sign-in. Please authenticate directly in your browser."
            }

        # Extract visible message rows
        script = """() => {
            const rows = Array.from(document.querySelectorAll('tr[role="row"]')).slice(0, 10);
            return rows.map(r => {
                const sender = r.querySelector('[email], .bDA, span.zF');
                const subject = r.querySelector('.bog, .bqe');
                const snippet = r.querySelector('.y2');
                return {
                    sender: sender ? sender.innerText.trim() : 'Unknown',
                    subject: subject ? subject.innerText.trim() : 'No subject',
                    snippet: snippet ? snippet.innerText.trim() : ''
                };
            }).filter(x => x.subject !== 'No subject');
        }"""
        messages = await page.evaluate(script)

        return {
            "status": "inbox_inspected",
            "message_count": len(messages),
            "messages": messages
        }

    async def search_mail(self, query: str) -> Dict[str, Any]:
        """Searches emails using the Gmail top search bar."""
        page = await self.browser.get_active_page()
        search_box = page.locator("input[aria-label*='Search mail' i], input[name='q']").first
        if await search_box.count() > 0:
            await search_box.fill(query)
            await search_box.press("Enter")
            await page.wait_for_timeout(1500)
            return {"status": "search_dispatched", "query": query}
        return {"status": "search_box_not_found"}
