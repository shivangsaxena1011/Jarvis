"""
SHIVANI App Adapter Base Interface
Defines uniform application control contracts across Desktop apps, Browser apps, and Mobile apps.
"""

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AppInfo(BaseModel):
    name: str
    display_name: str
    executable_path: Optional[str] = None
    app_type: str = "desktop"  # desktop, browser, mobile
    is_running: bool = False
    supported_actions: List[str] = Field(default_factory=list)


class AppAdapter(ABC):
    """Abstract adapter providing unified interaction contracts with local and remote apps."""

    name: str
    app_type: str = "desktop"  # "desktop" | "browser" | "mobile"

    def __init__(self):
        self.logger = logging.getLogger(f"shivani.adapters.{self.name}")

    @abstractmethod
    async def is_available(self) -> bool:
        """Checks if the application is installed or reachable on the current system."""
        pass

    @abstractmethod
    async def launch(self, **kwargs: Any) -> bool:
        """Launches or focuses the application."""
        pass

    @abstractmethod
    async def close(self) -> bool:
        """Terminates or closes the application."""
        pass

    @abstractmethod
    async def execute_action(self, action: str, **kwargs: Any) -> Any:
        """Executes a domain-specific action on the application."""
        pass

    @abstractmethod
    async def get_state(self) -> Dict[str, Any]:
        """Inspects current application window state, active tab/document, or UI status."""
        pass
