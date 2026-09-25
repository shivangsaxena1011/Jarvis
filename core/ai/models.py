"""Data models, descriptors, and enums for Phase 19: Local AI, Model Routing & Offline Autonomy."""

from __future__ import annotations

import enum
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


class ProviderType(str, enum.Enum):
    """Categorization of model provider architectures."""
    CLOUD = "cloud"
    LOCAL = "local"
    HYBRID = "hybrid"
    SPECIALIZED = "specialized"
    DETERMINISTIC = "deterministic"


class ModelCapability(str, enum.Enum):
    """Specific competencies verified for a model or engine."""
    SIMPLE_CONVERSATION = "simple_conversation"
    CLASSIFICATION = "classification"
    CODING = "coding"
    RESEARCH_SYNTHESIS = "research_synthesis"
    VISION = "vision"
    OCR = "ocr"
    PLANNING = "planning"
    TOOL_CALLING = "tool_calling"
    STRUCTURED_OUTPUT = "structured_output"
    FAST_INTENT = "fast_intent"
    CALCULATOR = "calculator"
    AUDIO_STT = "audio_stt"
    AUDIO_TTS = "audio_tts"
    EMBEDDINGS = "embeddings"
    RERANKING = "reranking"


class PrivacyLevel(str, enum.Enum):
    """Data sensitivity classification determining cloud vs local boundary."""
    PUBLIC = "public"                    # Open web data, public questions, non-sensitive queries -> Cloud permitted
    LOW_SENSITIVITY = "low_sensitivity"  # General user tasks without confidential data -> Cloud permitted
    PRIVATE = "private"                  # Personal files, local preferences -> Local preferred
    SENSITIVE = "sensitive"              # Codebase architectures, unreleased project docs -> Local preferred
    CRITICAL = "critical"                # Credentials, tokens, keys, banking, private health -> STRICTLY LOCAL


class ModelHealthState(str, enum.Enum):
    """Real-time operational status of an AI engine."""
    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    AUTH_REQUIRED = "auth_required"
    LOADING = "loading"
    ERROR = "error"


class RoutingStrategy(str, enum.Enum):
    """User-configurable routing heuristics."""
    AUTO = "auto"                    # Balanced smallest reliable model
    LOCAL_FIRST = "local_first"      # Always prefer local models if capable
    CLOUD_FIRST = "cloud_first"      # Prefer strong cloud models unless sensitive
    PRIVACY_FIRST = "privacy_first"  # Strict zero-cloud policy for anything non-public
    SPEED_FIRST = "speed_first"      # Optimize purely for lowest latency
    COST_AWARE = "cost_aware"        # Minimize cloud token usage and API costs


@dataclass
class HardwareProfile:
    """Hardware capabilities detected on the host workstation."""
    cpu_cores: int = 4
    cpu_model: str = "Unknown CPU"
    ram_total_gb: float = 16.0
    ram_available_gb: float = 8.0
    gpu_vendor: str = "None"         # "NVIDIA", "AMD", "Intel", "Apple", "None"
    gpu_model: str = "Integrated"
    vram_total_gb: float = 0.0
    vram_available_gb: float = 0.0
    storage_free_gb: float = 50.0
    os_platform: str = "Windows"
    has_cuda: bool = False
    recommended_local_size: str = "None"  # "None", "3B", "7B", "8B", "14B", "32B", "70B"

    @property
    def available_ram_gb(self) -> float:
        return self.ram_available_gb

    @property
    def total_ram_gb(self) -> float:
        return self.ram_total_gb

    @property
    def gpu_name(self) -> str:
        return self.gpu_model

    @property
    def gpu_vram_gb(self) -> float:
        return self.vram_total_gb

    @property
    def has_accelerator(self) -> bool:
        return self.has_cuda or self.gpu_vendor not in ("None", "", None)

    def to_dict(self) -> Dict[str, Any]:

        return {
            "cpu_cores": self.cpu_cores,
            "cpu_model": self.cpu_model,
            "ram_total_gb": round(self.ram_total_gb, 2),
            "ram_available_gb": round(self.ram_available_gb, 2),
            "gpu_vendor": self.gpu_vendor,
            "gpu_model": self.gpu_model,
            "vram_total_gb": round(self.vram_total_gb, 2),
            "vram_available_gb": round(self.vram_available_gb, 2),
            "storage_free_gb": round(self.storage_free_gb, 2),
            "os_platform": self.os_platform,
            "has_cuda": self.has_cuda,
            "recommended_local_size": self.recommended_local_size,
        }


@dataclass
class ModelDescriptor:
    """Complete specification of a model registered in the mesh."""
    model_id: str
    name: str
    provider_id: str
    provider_type: ProviderType
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    context_window: int = 8192
    has_vision: bool = False
    has_audio: bool = False
    has_tools: bool = True
    has_structured_output: bool = True
    reasoning_score: float = 0.5     # 0.0 to 1.0 relative strength
    coding_score: float = 0.5
    speed_tokens_per_sec: float = 35.0
    latency_ms_p50: float = 400.0
    cost_per_1k_input: float = 0.0   # USD per 1000 input tokens
    cost_per_1k_output: float = 0.0
    min_ram_gb: float = 4.0
    min_vram_gb: float = 0.0
    health_state: ModelHealthState = ModelHealthState.AVAILABLE
    metadata: Dict[str, Any] = field(default_factory=dict)

    def supports_capability(self, cap: ModelCapability | str) -> bool:
        cap_val = cap.value if isinstance(cap, ModelCapability) else cap
        return cap_val in self.capabilities

    def is_local(self) -> bool:
        return self.provider_type in (ProviderType.LOCAL, ProviderType.DETERMINISTIC)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "name": self.name,
            "provider_id": self.provider_id,
            "provider_type": self.provider_type.value,
            "version": self.version,
            "capabilities": self.capabilities,
            "context_window": self.context_window,
            "has_vision": self.has_vision,
            "has_audio": self.has_audio,
            "has_tools": self.has_tools,
            "has_structured_output": self.has_structured_output,
            "reasoning_score": self.reasoning_score,
            "coding_score": self.coding_score,
            "speed_tokens_per_sec": self.speed_tokens_per_sec,
            "latency_ms_p50": self.latency_ms_p50,
            "cost_per_1k_input": self.cost_per_1k_input,
            "cost_per_1k_output": self.cost_per_1k_output,
            "min_ram_gb": self.min_ram_gb,
            "min_vram_gb": self.min_vram_gb,
            "health_state": self.health_state.value,
            "metadata": self.metadata,
        }


@dataclass
class RoutingDecision:
    """The reasoned result of a model routing evaluation."""
    task_type: str
    selected_model_id: str
    fallback_model_id: Optional[str]
    provider_type: ProviderType
    is_deterministic: bool = False
    confidence_score: float = 1.0
    reason: str = ""
    privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC
    applied_policies: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_type": self.task_type,
            "selected_model_id": self.selected_model_id,
            "fallback_model_id": self.fallback_model_id,
            "provider_type": self.provider_type.value,
            "is_deterministic": self.is_deterministic,
            "confidence_score": round(self.confidence_score, 2),
            "reason": self.reason,
            "privacy_level": self.privacy_level.value,
            "applied_policies": self.applied_policies,
            "constraints": self.constraints,
            "timestamp": self.timestamp,
        }


@dataclass
class AIUsageMetrics:
    """Live aggregation of token usage, requests, costs, and latency."""
    local_requests: int = 0
    cloud_requests: int = 0
    deterministic_requests: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost_usd: float = 0.0
    total_latency_ms: float = 0.0

    @property
    def total_requests(self) -> int:
        return self.local_requests + self.cloud_requests + self.deterministic_requests

    @property
    def average_latency_ms(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return round(self.total_latency_ms / self.total_requests, 1)

    def record_request(
        self,
        provider_type: ProviderType,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = 0.0,
    ) -> None:
        if provider_type == ProviderType.LOCAL:
            self.local_requests += 1
        elif provider_type == ProviderType.CLOUD:
            self.cloud_requests += 1
        else:
            self.deterministic_requests += 1

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.estimated_cost_usd += cost_usd
        self.total_latency_ms += latency_ms

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "local_requests": self.local_requests,
            "cloud_requests": self.cloud_requests,
            "deterministic_requests": self.deterministic_requests,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "estimated_cost_usd": round(self.estimated_cost_usd, 4),
            "average_latency_ms": self.average_latency_ms,
        }


@dataclass
class BenchmarkResult:
    """Empirical performance metrics captured from running a model."""
    model_id: str
    tokens_per_second: float
    latency_first_token_ms: float
    total_time_ms: float
    tool_calling_passed: bool
    structured_output_passed: bool
    memory_used_mb: float = 0.0
    vram_used_mb: float = 0.0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "tokens_per_second": round(self.tokens_per_second, 1),
            "latency_first_token_ms": round(self.latency_first_token_ms, 1),
            "total_time_ms": round(self.total_time_ms, 1),
            "tool_calling_passed": self.tool_calling_passed,
            "structured_output_passed": self.structured_output_passed,
            "memory_used_mb": round(self.memory_used_mb, 1),
            "vram_used_mb": round(self.vram_used_mb, 1),
            "timestamp": self.timestamp,
        }
