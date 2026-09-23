"""
Unit tests for SHIVANI LLM Provider Abstraction.
"""

import pytest
from core.config import Settings
from core.llm.base import TaskPlan, PlanStep
from core.llm.mock_provider import MockLLMProvider
from core.llm.factory import create_llm_provider


@pytest.mark.asyncio
async def test_mock_llm_provider_text():
    provider = MockLLMProvider()
    resp = await provider.generate_text("Hello Shivani")
    assert "SHIVANI" in resp


@pytest.mark.asyncio
async def test_mock_llm_provider_plan_generation():
    provider = MockLLMProvider()
    plan = await provider.generate_plan(
        user_query="Shivani, open notepad and check active window",
        available_tools=[{"name": "computer.open_app"}, {"name": "computer.get_active_window"}]
    )

    assert isinstance(plan, TaskPlan)
    assert len(plan.steps) == 2
    assert plan.steps[0].tool == "computer.open_app"
    assert plan.steps[1].tool == "computer.get_active_window"


def test_llm_factory_fallback():
    settings = Settings(LLM_PROVIDER="mock")
    provider = create_llm_provider(settings)
    assert isinstance(provider, MockLLMProvider)

    # Empty key fallback to mock with warning
    settings_gemini_no_key = Settings(LLM_PROVIDER="gemini", GEMINI_API_KEY="")
    provider_fallback = create_llm_provider(settings_gemini_no_key)
    assert isinstance(provider_fallback, MockLLMProvider)
