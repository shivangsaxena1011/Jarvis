"""Model Registry for Phase 19: Cataloging, Versioning & Model Tracking.

Maintains metadata, verified capabilities, context limits, costs, and hardware constraints
for all available cloud, local, and deterministic models in Shivani's mesh.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

from core.ai.models import (
    ModelCapability,
    ModelDescriptor,
    ModelHealthState,
    ProviderType,
)

logger = logging.getLogger("shivani.ai.registry")


class ModelRegistry:
    """Central catalog for discovering, indexing, and querying AI models."""

    def __init__(self):
        self._lock = threading.RLock()
        self._models: Dict[str, ModelDescriptor] = {}
        self._pinned_models: Dict[str, str] = {}
        self._init_default_catalog()

    def _init_default_catalog(self) -> None:
        """Seed registry with standard cloud, local, and deterministic engines."""
        defaults = [
            # Deterministic Engines
            ModelDescriptor(
                model_id="deterministic-calc",
                name="Deterministic Math Calculator",
                provider_id="builtin-math",
                provider_type=ProviderType.DETERMINISTIC,
                capabilities=[ModelCapability.CALCULATOR.value],
                context_window=1024,
                speed_tokens_per_sec=1000.0,
                latency_ms_p50=1.0,
                reasoning_score=1.0,
                coding_score=0.0,
            ),
            ModelDescriptor(
                model_id="fast-intent-parser",
                name="Fast Regex & Rule Intent Classifier",
                provider_id="builtin-intent",
                provider_type=ProviderType.DETERMINISTIC,
                capabilities=[ModelCapability.FAST_INTENT.value, ModelCapability.CLASSIFICATION.value],
                context_window=2048,
                speed_tokens_per_sec=800.0,
                latency_ms_p50=5.0,
                reasoning_score=0.7,
                coding_score=0.0,
            ),

            # Local Small (Runs on >= 8GB RAM, CPU or small GPU)
            ModelDescriptor(
                model_id="phi3:mini",
                name="Phi-3 Mini (3.8B)",
                provider_id="ollama",
                provider_type=ProviderType.LOCAL,
                capabilities=[
                    ModelCapability.SIMPLE_CONVERSATION.value,
                    ModelCapability.CLASSIFICATION.value,
                    ModelCapability.FAST_INTENT.value,
                ],
                context_window=4096,
                min_ram_gb=4.0,
                min_vram_gb=2.0,
                speed_tokens_per_sec=40.0,
                latency_ms_p50=250.0,
                reasoning_score=0.55,
                coding_score=0.45,
            ),

            # Local General (Runs on >= 16GB RAM or 8GB VRAM)
            ModelDescriptor(
                model_id="llama3.1:8b",
                name="Llama 3.1 8B Instruct",
                provider_id="ollama",
                provider_type=ProviderType.LOCAL,
                capabilities=[
                    ModelCapability.SIMPLE_CONVERSATION.value,
                    ModelCapability.CLASSIFICATION.value,
                    ModelCapability.CODING.value,
                    ModelCapability.PLANNING.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=16384,
                min_ram_gb=8.0,
                min_vram_gb=5.0,
                speed_tokens_per_sec=32.0,
                latency_ms_p50=400.0,
                reasoning_score=0.78,
                coding_score=0.74,
            ),
            ModelDescriptor(
                model_id="qwen2.5:7b",
                name="Qwen 2.5 7B",
                provider_id="ollama",
                provider_type=ProviderType.LOCAL,
                capabilities=[
                    ModelCapability.SIMPLE_CONVERSATION.value,
                    ModelCapability.CODING.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=32768,
                min_ram_gb=8.0,
                min_vram_gb=5.0,
                speed_tokens_per_sec=35.0,
                latency_ms_p50=350.0,
                reasoning_score=0.80,
                coding_score=0.79,
            ),

            # Local Coding Specialist
            ModelDescriptor(
                model_id="qwen2.5-coder:7b",
                name="Qwen 2.5 Coder 7B",
                provider_id="ollama",
                provider_type=ProviderType.LOCAL,
                capabilities=[
                    ModelCapability.CODING.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=32768,
                min_ram_gb=8.0,
                min_vram_gb=5.0,
                speed_tokens_per_sec=34.0,
                latency_ms_p50=380.0,
                reasoning_score=0.82,
                coding_score=0.88,
            ),

            # Cloud General
            ModelDescriptor(
                model_id="gemini-2.5-flash",
                name="Gemini 2.5 Flash",
                provider_id="gemini",
                provider_type=ProviderType.CLOUD,
                capabilities=[
                    ModelCapability.SIMPLE_CONVERSATION.value,
                    ModelCapability.CLASSIFICATION.value,
                    ModelCapability.CODING.value,
                    ModelCapability.RESEARCH_SYNTHESIS.value,
                    ModelCapability.VISION.value,
                    ModelCapability.PLANNING.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=1000000,
                has_vision=True,
                speed_tokens_per_sec=80.0,
                latency_ms_p50=350.0,
                cost_per_1k_input=0.0001,
                cost_per_1k_output=0.0004,
                reasoning_score=0.88,
                coding_score=0.85,
            ),
            ModelDescriptor(
                model_id="gpt-4o",
                name="OpenAI GPT-4o",
                provider_id="openai",
                provider_type=ProviderType.CLOUD,
                capabilities=[
                    ModelCapability.SIMPLE_CONVERSATION.value,
                    ModelCapability.CLASSIFICATION.value,
                    ModelCapability.CODING.value,
                    ModelCapability.RESEARCH_SYNTHESIS.value,
                    ModelCapability.VISION.value,
                    ModelCapability.PLANNING.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=128000,
                has_vision=True,
                speed_tokens_per_sec=65.0,
                latency_ms_p50=500.0,
                cost_per_1k_input=0.0025,
                cost_per_1k_output=0.010,
                reasoning_score=0.92,
                coding_score=0.90,
            ),

            # Cloud Heavy Reasoning
            ModelDescriptor(
                model_id="gemini-1.5-pro",
                name="Gemini 1.5 Pro",
                provider_id="gemini",
                provider_type=ProviderType.CLOUD,
                capabilities=[
                    ModelCapability.CODING.value,
                    ModelCapability.RESEARCH_SYNTHESIS.value,
                    ModelCapability.PLANNING.value,
                    ModelCapability.VISION.value,
                    ModelCapability.TOOL_CALLING.value,
                    ModelCapability.STRUCTURED_OUTPUT.value,
                ],
                context_window=2000000,
                has_vision=True,
                speed_tokens_per_sec=40.0,
                latency_ms_p50=900.0,
                cost_per_1k_input=0.00125,
                cost_per_1k_output=0.005,
                reasoning_score=0.95,
                coding_score=0.93,
            ),

            # Specialized Multimodal
            ModelDescriptor(
                model_id="whisper-local",
                name="faster-whisper Small",
                provider_id="local-audio",
                provider_type=ProviderType.SPECIALIZED,
                capabilities=[ModelCapability.AUDIO_STT.value],
                min_ram_gb=4.0,
                speed_tokens_per_sec=100.0,
                latency_ms_p50=300.0,
            ),
            ModelDescriptor(
                model_id="piper-tts-local",
                name="Piper Local Neural TTS",
                provider_id="local-audio",
                provider_type=ProviderType.SPECIALIZED,
                capabilities=[ModelCapability.AUDIO_TTS.value],
                min_ram_gb=2.0,
                speed_tokens_per_sec=150.0,
                latency_ms_p50=150.0,
            ),
            ModelDescriptor(
                model_id="paddle-ocr-local",
                name="PaddleOCR / Tesseract Local Engine",
                provider_id="local-vision",
                provider_type=ProviderType.SPECIALIZED,
                capabilities=[ModelCapability.OCR.value],
                min_ram_gb=4.0,
                speed_tokens_per_sec=80.0,
                latency_ms_p50=200.0,
            ),
        ]

        for m in defaults:
            self._models[m.model_id] = m

    def register_model(self, descriptor: ModelDescriptor) -> None:
        with self._lock:
            self._models[descriptor.model_id] = descriptor
            logger.info(f"Registered model '{descriptor.model_id}' ({descriptor.provider_type.value})")

    def get_model(self, model_id: str) -> Optional[ModelDescriptor]:
        with self._lock:
            return self._models.get(model_id)

    def list_models(
        self,
        provider_type: Optional[ProviderType] = None,
        capability: Optional[ModelCapability | str] = None,
        max_ram_gb: Optional[float] = None,
        max_vram_gb: Optional[float] = None,
    ) -> List[ModelDescriptor]:
        with self._lock:
            results = list(self._models.values())

            if provider_type:
                results = [m for m in results if m.provider_type == provider_type]

            if capability:
                cap_val = capability.value if isinstance(capability, ModelCapability) else capability
                results = [m for m in results if m.supports_capability(cap_val)]

            if max_ram_gb is not None:
                results = [m for m in results if m.min_ram_gb <= max_ram_gb]

            if max_vram_gb is not None:
                results = [m for m in results if m.min_vram_gb <= max_vram_gb]

            return results

    def update_health(self, model_id: str, new_health: ModelHealthState) -> bool:
        with self._lock:
            model = self._models.get(model_id)
            if not model:
                return False
            model.health_state = new_health
            logger.info(f"Updated health for {model_id} -> {new_health.value}")
            return True

    def pin_model(self, workflow_name: str, model_id: str) -> bool:
        with self._lock:
            if model_id not in self._models:
                raise ValueError(f"Cannot pin unknown model '{model_id}'")
            self._pinned_models[workflow_name] = model_id
            logger.info(f"Pinned workflow '{workflow_name}' to model '{model_id}'")
            return True

    def get_pinned_model(self, workflow_name: str) -> Optional[str]:
        with self._lock:
            return self._pinned_models.get(workflow_name)
