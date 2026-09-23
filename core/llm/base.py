"""
SHIVANI LLM Provider Abstraction
Defines the base interface for language model providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PlanStep(BaseModel):
    id: str
    tool: str
    action: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    requires_confirmation: bool = False
    expected_outcome: str = ""


class TaskPlan(BaseModel):
    goal: str
    rationale: str = ""
    steps: List[PlanStep] = Field(default_factory=list)


class LLMProvider(ABC):
    """Abstract interface for all AI model providers."""

    @abstractmethod
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generates plain text response."""
        pass

    @abstractmethod
    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """Generates a structured multi-step task execution plan."""
        pass
