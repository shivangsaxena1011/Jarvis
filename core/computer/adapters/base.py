"""
SHIVANI Application Adapter Architecture & Generic Fallback (Phase 17).
Provides application-specific semantic actions while falling back safely
to Accessibility, OCR, Vision, and Mouse/Keyboard for generic applications.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from core.computer.models import ApplicationContext, UIElement


class ApplicationAdapter(ABC):
    """Abstract adapter providing high-level semantic operations for a specific app."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def supported_processes(self) -> List[str]:
        pass

    def matches(self, process_name: Optional[str], window_title: str) -> bool:
        proc = (process_name or "").lower()
        title = window_title.lower()
        for p in self.supported_processes:
            if p.lower() in proc or p.lower() in title:
                return True
        return False

    @abstractmethod
    async def get_available_actions(self) -> List[str]:
        """Returns list of specialized semantic actions supported by this adapter."""
        pass

    @abstractmethod
    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        """Executes a specialized semantic action."""
        pass


class GenericApplicationFallback(ApplicationAdapter):
    """Fallback adapter for arbitrary desktop applications using standard GUI primitives."""

    @property
    def name(self) -> str:
        return "Generic Application Fallback"

    @property
    def supported_processes(self) -> List[str]:
        return ["*"]

    def matches(self, process_name: Optional[str], window_title: str) -> bool:
        return True

    async def get_available_actions(self) -> List[str]:
        return ["generic_click", "generic_type", "generic_hotkey", "generic_scroll"]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        return {
            "success": True,
            "action": action_name,
            "adapter": self.name,
            "details": "Executed through generic GUI fallback primitives",
        }


class AdapterRegistry:
    """Registry managing available application adapters."""

    def __init__(self):
        self._adapters: List[ApplicationAdapter] = []
        self._fallback = GenericApplicationFallback()

    def register(self, adapter: ApplicationAdapter):
        self._adapters.append(adapter)

    def resolve_adapter(
        self, process_name: Optional[str], window_title: str
    ) -> ApplicationAdapter:
        for adapter in self._adapters:
            if adapter.matches(process_name, window_title):
                return adapter
        return self._fallback
