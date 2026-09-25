"""Unit tests for Phase 19 Model Registry and Providers."""

import pytest
from core.ai.models import (
    ModelCapability,
    ModelDescriptor,
    ModelHealthState,
    ProviderType,
)
from core.ai.registry import ModelRegistry
from core.ai.matrix import CapabilityMatrix
from core.ai.hardware import detect_hardware


def test_registry_initialization_contains_default_models():
    reg = ModelRegistry()
    models = reg.list_models()
    assert len(models) >= 10
    model_ids = [m.model_id for m in models]
    assert "deterministic-calc" in model_ids
    assert "phi3:mini" in model_ids
    assert "llama3.1:8b" in model_ids
    assert "gemini-2.5-flash" in model_ids


def test_registry_filter_by_provider():
    reg = ModelRegistry()
    local_models = reg.list_models(provider_type=ProviderType.LOCAL)
    assert len(local_models) >= 3
    assert all(m.provider_type == ProviderType.LOCAL for m in local_models)

    cloud_models = reg.list_models(provider_type=ProviderType.CLOUD)
    assert len(cloud_models) >= 3
    assert all(m.provider_type == ProviderType.CLOUD for m in cloud_models)


def test_registry_register_and_health_state():
    reg = ModelRegistry()
    custom_desc = ModelDescriptor(
        model_id="deepseek-coder:6.7b",
        name="DeepSeek Coder 6.7B",
        provider_id="local_ollama",
        provider_type=ProviderType.LOCAL,
        capabilities=[ModelCapability.CODING.value, ModelCapability.STRUCTURED_OUTPUT.value],
        context_window=16384,
        min_ram_gb=8.0,
    )
    reg.register_model(custom_desc)
    assert reg.get_model("deepseek-coder:6.7b") is not None

    reg.update_health("deepseek-coder:6.7b", ModelHealthState.DEGRADED)
    m = reg.get_model("deepseek-coder:6.7b")
    assert m.health_state == ModelHealthState.DEGRADED


def test_capability_matrix_find_candidates():
    reg = ModelRegistry()
    matrix = CapabilityMatrix(registry=reg)
    hw = detect_hardware()

    coding_candidates = matrix.find_candidates(
        required_capabilities=[ModelCapability.CODING.value],
        hardware_profile=hw,
        allow_cloud=True,
    )
    assert len(coding_candidates) > 0
    assert any(m.model_id in ("qwen2.5-coder:7b", "gpt-4o", "gemini-1.5-pro") for m in coding_candidates)


def test_capability_matrix_enforce_local_only():
    reg = ModelRegistry()
    matrix = CapabilityMatrix(registry=reg)
    hw = detect_hardware()

    local_candidates = matrix.find_candidates(
        required_capabilities=[ModelCapability.SIMPLE_CONVERSATION.value],
        hardware_profile=hw,
        allow_cloud=False,
        require_local=True,
    )
    assert len(local_candidates) > 0
    assert all(m.provider_type == ProviderType.LOCAL for m in local_candidates)
