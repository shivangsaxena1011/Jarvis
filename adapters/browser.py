"""
SHIVANI Browser Application Adapter
Adapter bridging browser sessions and web applications into the uniform AppAdapter model.
"""

from typing import Any, Dict, Optional
from adapters.base import AppAdapter


class BrowserAppAdapter(AppAdapter):
    """Adapter for web applications and browser automation workflows."""

    def __init__(self, browser_agent: Optional[Any] = None):
        self.name = "browser"
        self.app_type = "browser"
        super().__init__()
        self.browser_agent = browser_agent

    async def is_available(self) -> bool:
        return True

    async def launch(self, **kwargs: Any) -> bool:
        url = kwargs.get("url", "https://google.com")
        if self.browser_agent and hasattr(self.browser_agent, "navigate"):
            try:
                await self.browser_agent.navigate(url)
                return True
            except Exception as e:
                self.logger.error(f"Failed to navigate browser to {url}: {e}")
                return False
        return True

    async def close(self) -> bool:
        if self.browser_agent and hasattr(self.browser_agent, "close"):
            try:
                await self.browser_agent.close()
                return True
            except Exception as e:
                self.logger.warning(f"Error closing browser: {e}")
        return True

    async def execute_action(self, action: str, **kwargs: Any) -> Any:
        if action == "navigate":
            return await self.launch(url=kwargs.get("url", ""))
        elif action == "close":
            return await self.close()
        elif action == "extract":
            if self.browser_agent and hasattr(self.browser_agent, "extract_content"):
                return await self.browser_agent.extract_content()
            return {"content": "Sample extracted content"}
        return {"action": action, "status": "executed"}

    async def get_state(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.app_type,
            "is_running": self.browser_agent is not None,
        }
