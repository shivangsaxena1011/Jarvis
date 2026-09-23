"""
SHIVANI LLM Provider Abstraction
Defines the base interface for model providers: generate, generate_structured, stream, health_check.
"""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Type
from pydantic import BaseModel
from core.tasks.task import TaskPlan


class LLMProvider(ABC):
    """Abstract interface for all model backends."""

    name: str = "base"

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        """Generate plain text response from the model."""
        pass

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        """Generate response strictly adhering to a Pydantic schema."""
        pass

    @abstractmethod
    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        """Decomposes user query into a verified TaskPlan."""
        pass

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> AsyncIterator[str]:
        """Stream response tokens asynchronously (default fallback yields full text)."""
        text = await self.generate(prompt, system_prompt=system_prompt)
        yield text

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Perform a low-overhead health/liveness check on the provider."""
        pass

    # Backward compatibility aliases
    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.2) -> str:
        return await self.generate(prompt, system_prompt=system_prompt, temperature=temperature)
