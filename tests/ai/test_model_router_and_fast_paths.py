"""Unit tests for Model Router, Fast Paths, and Multi-Factor Scoring."""

import pytest
from core.ai.models import PrivacyLevel, ProviderType, RoutingStrategy
from core.ai.registry import ModelRegistry
from core.ai.router import ModelRouter


@pytest.fixture
def router():
    reg = ModelRegistry()
    return ModelRouter(registry=reg)


def test_deterministic_calculator_fast_path(router):
    decision = router.route("calculate 25 * 4 + 10")
    assert decision.is_deterministic is True
    assert decision.selected_model_id == "deterministic-calc"
    assert decision.provider_type == ProviderType.DETERMINISTIC
    assert decision.confidence_score == 1.0
    assert "deterministic_fast_path" in decision.applied_policies


def test_desktop_command_fast_path(router):
    commands = ["open chrome", "take screenshot", "close window", "open notepad"]
    for cmd in commands:
        decision = router.route(cmd)
        assert decision.is_deterministic is True
        assert decision.selected_model_id == "fast-intent-parser"
        assert decision.provider_type == ProviderType.DETERMINISTIC
        assert "intent_fast_path" in decision.applied_policies


def test_coding_query_routes_to_coder_model(router):
    code_prompt = "def binary_search(arr, target): find bug in this function"
    decision = router.route(code_prompt)
    assert decision.is_deterministic is False
    assert "coding" in decision.constraints["required_capabilities"]
    assert decision.selected_model_id in ("qwen2.5-coder:7b", "gpt-4o", "gemini-1.5-pro")


def test_local_first_strategy(router):
    prompt = "Explain how event buses decouple microservices"
    decision = router.route(prompt, strategy_override=RoutingStrategy.LOCAL_FIRST)
    assert decision.provider_type == ProviderType.LOCAL
    assert decision.selected_model_id in ("llama3.1:8b", "phi3:mini", "qwen2.5:7b")


def test_privacy_first_strategy_bars_cloud(router):
    prompt = "Summarize the key architectural patterns in distributed databases"
    decision = router.route(prompt, strategy_override=RoutingStrategy.PRIVACY_FIRST)
    assert decision.constraints["allow_cloud"] is False
    assert decision.provider_type == ProviderType.LOCAL


def test_fallback_model_present(router):
    prompt = "Write an essay about renewable energy options"
    decision = router.route(prompt)
    assert decision.fallback_model_id is not None
    assert decision.fallback_model_id != decision.selected_model_id
