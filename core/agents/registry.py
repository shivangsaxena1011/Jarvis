"""
SHIVANI Unified Agent Registry
Maintains registry of specialized autonomous sub-agents with capability metadata,
intent routing, and message dispatch.
"""

from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from core.agents.communication import AgentMessage, AgentResponse


class AgentDescriptor(BaseModel):
    name: str
    description: str
    capabilities: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    risk_tier: str = "SAFE" # "SAFE" | "SENSITIVE" | "CRITICAL"


class AgentRegistry:
    def __init__(self):
        self._agents: Dict[str, Any] = {}
        self._descriptors: Dict[str, AgentDescriptor] = {}
        self._handlers: Dict[str, Callable[[AgentMessage], Any]] = {}

    def register_agent(
        self,
        descriptor: AgentDescriptor,
        instance: Any,
        message_handler: Optional[Callable[[AgentMessage], Any]] = None,
    ) -> None:
        self._agents[descriptor.name] = instance
        self._descriptors[descriptor.name] = descriptor
        if message_handler:
            self._handlers[descriptor.name] = message_handler

    def unregister_agent(self, name: str) -> bool:
        """Unregisters an agent, its descriptor, and its message handler."""
        removed = False
        if name in self._agents:
            del self._agents[name]
            removed = True
        if name in self._descriptors:
            del self._descriptors[name]
            removed = True
        if name in self._handlers:
            del self._handlers[name]
        return removed

    def get_agent(self, name: str) -> Optional[Any]:
        return self._agents.get(name)

    def get_descriptor(self, name: str) -> Optional[AgentDescriptor]:
        return self._descriptors.get(name)

    def list_descriptors(self) -> List[AgentDescriptor]:
        return list(self._descriptors.values())

    def match_agent(self, query: str) -> str:
        """Determines best matching sub-agent based on query keywords and intent signals."""
        q_lower = query.lower()

        # Phone / Mobile signals
        if any(w in q_lower for w in ["phone", "mobile", "android", "insta", "whatsapp", "settings kholo"]):
            if "phone_agent" in self._agents:
                return "phone_agent"

        # Presentation signals
        if any(w in q_lower for w in ["presentation", "ppt", "slide", "pitch deck", "slides"]):
            if "presentation_agent" in self._agents:
                return "presentation_agent"

        # Documentation signals
        if any(w in q_lower for w in ["readme", "api doc", "architecture doc", "documentation"]):
            if "documentation_agent" in self._agents:
                return "documentation_agent"

        # Coding signals
        if any(w in q_lower for w in ["code", "bug", "patch", "git", "commit", "test run", "build", "refactor"]):
            if "coding_agent" in self._agents:
                return "coding_agent"

        # Research signals
        if any(w in q_lower for w in ["research", "summarize paper", "arxiv", "compare", "literature"]):
            if "research_agent" in self._agents:
                return "research_agent"

        # Browser signals
        if any(w in q_lower for w in ["browser", "chrome", "youtube", "website", "search web", "linkedin", "gmail"]):
            if "browser_agent" in self._agents:
                return "browser_agent"

        # Desktop / Computer default
        return "computer_agent" if "computer_agent" in self._agents else "orchestrator"

    async def dispatch_message(self, message: AgentMessage) -> AgentResponse:
        """Dispatches an inter-agent message to target agent's registered handler."""
        handler = self._handlers.get(message.recipient)
        if not handler:
            return AgentResponse.failed(f"Recipient agent '{message.recipient}' not found or has no message handler.")

        try:
            res = handler(message)
            if hasattr(res, "__await__"):
                res = await res
            if isinstance(res, AgentResponse):
                return res
            elif isinstance(res, dict):
                return AgentResponse.success(summary="Handled successfully", data=res)
            return AgentResponse.success(summary=str(res))
        except Exception as e:
            return AgentResponse.failed(f"Inter-agent dispatch failed: {e}")
