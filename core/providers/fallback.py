"""
SHIVANI Model Fallback Chain Provider
Orchestrates an ordered list of LLM providers. If the primary provider experiences
rate limits, authentication errors, or network outages, execution gracefully
cascades down the fallback chain.
"""

import logging
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel

from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan
from core.errors import ProviderError

logger = logging.getLogger("shivani.providers.fallback")


class FallbackProviderChain(LLMProvider):
    name = "fallback_chain"

    def __init__(self, providers: List[LLMProvider]):
        if not providers:
            raise ValueError("FallbackProviderChain requires at least one provider.")
        self.providers = providers

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                return await provider.generate(prompt, system_prompt=system_prompt, temperature=temperature)
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider %s (index %d) failed during generate: %s. Trying next provider...",
                    getattr(provider, "name", type(provider).__name__), i, e
                )
        raise ProviderError(f"All providers in fallback chain failed: {last_error}")

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                return await provider.generate_structured(prompt, schema=schema, system_prompt=system_prompt)
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider %s (index %d) failed during generate_structured: %s. Trying next provider...",
                    getattr(provider, "name", type(provider).__name__), i, e
                )
        raise ProviderError(f"All providers in fallback chain failed during structured generation: {last_error}")

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        last_error = None
        for i, provider in enumerate(self.providers):
            try:
                return await provider.generate_plan(user_query, available_tools=available_tools, context=context)
            except Exception as e:
                last_error = e
                logger.warning(
                    "Provider %s (index %d) failed during generate_plan: %s. Trying next provider...",
                    getattr(provider, "name", type(provider).__name__), i, e
                )
        raise ProviderError(f"All providers in fallback chain failed during plan generation: {last_error}")

    async def health_check(self) -> Dict[str, Any]:
        results = []
        any_healthy = False
        for provider in self.providers:
            try:
                hc = await provider.health_check()
                results.append(hc)
                if hc.get("healthy", False):
                    any_healthy = True
            except Exception as e:
                results.append({"healthy": False, "error": str(e), "provider": getattr(provider, "name", "unknown")})

        return {
            "healthy": any_healthy,
            "provider": "fallback_chain",
            "chain_length": len(self.providers),
            "providers_status": results,
        }
