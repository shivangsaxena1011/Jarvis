"""Shivani AI Subsystem for Phase 19.

Local AI, Multi-Factor Model Routing, Performance Engineering,
Privacy Boundary, and Offline Autonomy.
"""

from core.ai.benchmark import ModelBenchmarkSuite
from core.ai.cache import SemanticCache
from core.ai.context_manager import ContextManager, ConversationContext
from core.ai.doctor import AIDoctor
from core.ai.hardware import HardwareProfiler
from core.ai.local_runtime import (
    LocalModelRuntime,
    MockLocalRuntime,
    OllamaLocalRuntime,
)
from core.ai.matrix import CapabilityMatrix
from core.ai.models import (
    AIUsageMetrics,
    BenchmarkResult,
    HardwareProfile,
    ModelCapability,
    ModelDescriptor,
    ModelHealthState,
    PrivacyLevel,
    ProviderType,
    RoutingDecision,
    RoutingStrategy,
)
from core.ai.offline import OfflineManager
from core.ai.privacy import CloudContextFilter, DataClassifier
from core.ai.registry import ModelRegistry
from core.ai.resource_manager import ModelResourceManager
from core.ai.router import ModelRouter
from core.ai.security import ModelSecurityBoundary
from core.ai.specialized_routing import MultimodalRouter

__all__ = [
    "ProviderType",
    "ModelCapability",
    "PrivacyLevel",
    "ModelHealthState",
    "RoutingStrategy",
    "HardwareProfile",
    "ModelDescriptor",
    "RoutingDecision",
    "AIUsageMetrics",
    "BenchmarkResult",
    "HardwareProfiler",
    "ModelRegistry",
    "CapabilityMatrix",
    "LocalModelRuntime",
    "OllamaLocalRuntime",
    "MockLocalRuntime",
    "DataClassifier",
    "CloudContextFilter",
    "ModelRouter",
    "ModelResourceManager",
    "OfflineManager",
    "ContextManager",
    "ConversationContext",
    "SemanticCache",
    "MultimodalRouter",
    "ModelSecurityBoundary",
    "ModelBenchmarkSuite",
    "AIDoctor",
]
