"""
Unit tests for SHIVANI Model Providers.
"""

import pytest
from pydantic import BaseModel
from core.config import Settings
from core.providers.mock import MockProvider
from core.providers.gemini import GeminiProvider
from core.providers.factory import create_provider
from core.tasks.task import TaskPlan


class DummySchema(BaseModel):
    summary: str = "ok"
    value: int = 42



@pytest.mark.asyncio
async def test_mock_provider_lifecycle():
    provider = MockProvider()
    
    # 1. Text generation
    text = await provider.generate("hello")
    assert "SHIVANI" in text

    # 2. Plan generation
    plan = await provider.generate_plan("Open Chrome", available_tools=[])
    assert isinstance(plan, TaskPlan)
    assert len(plan.steps) == 2
    assert plan.steps[0].tool == "computer.open_app"

    # 3. Stream
    tokens = []
    async for token in provider.stream("ping"):
        tokens.append(token)
    assert len(tokens) >= 1

    # 4. Health check
    health = await provider.health_check()
    assert health["healthy"] is True
    assert health["provider"] == "mock"


@pytest.mark.asyncio
async def test_gemini_provider_unconfigured_health():
    provider = GeminiProvider(api_key="")
    health = await provider.health_check()
    assert health["healthy"] is False
    assert "GEMINI_API_KEY is not set" in health["error"]


def test_provider_factory():
    settings = Settings(LLM_PROVIDER="mock")
    p = create_provider(settings)
    assert isinstance(p, MockProvider)
