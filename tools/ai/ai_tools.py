"""AI Routing, Performance & Offline Autonomy Tools for Phase 19.

Exposes AI subsystem status, multi-factor model routing, local model benchmarking,
AI Doctor diagnostics, offline autonomy controls, and model registry inspection
to the Tool Registry and Orchestrator.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from core.ai.benchmark import ModelBenchmarkSuite
from core.ai.doctor import AIDoctor
from core.ai.hardware import HardwareProfiler
from core.ai.local_runtime import LocalModelRuntime, MockLocalRuntime, OllamaLocalRuntime
from core.ai.models import PrivacyLevel, ProviderType
from core.ai.offline import OfflineManager
from core.ai.registry import ModelRegistry
from core.ai.resource_manager import ModelResourceManager
from core.ai.router import ModelRouter
from security.permissions.engine import RiskLevel
from tools.base import BaseTool, ToolResult

# Global singletons for tools
_ai_registry: Optional[ModelRegistry] = None
_ai_router: Optional[ModelRouter] = None
_ai_offline: Optional[OfflineManager] = None
_ai_benchmark: Optional[ModelBenchmarkSuite] = None
_ai_doctor: Optional[AIDoctor] = None
_ai_runtime: Optional[LocalModelRuntime] = None
_ai_resources: Optional[ModelResourceManager] = None


def get_ai_registry() -> ModelRegistry:
    global _ai_registry
    if _ai_registry is None:
        _ai_registry = ModelRegistry()
    return _ai_registry


def get_ai_runtime() -> LocalModelRuntime:
    global _ai_runtime
    if _ai_runtime is None:
        ollama = OllamaLocalRuntime()
        if ollama.is_runtime_available():
            _ai_runtime = ollama
        else:
            _ai_runtime = MockLocalRuntime(available=True)
    return _ai_runtime


def set_ai_runtime(runtime: LocalModelRuntime) -> None:
    global _ai_runtime, _ai_router, _ai_doctor, _ai_benchmark, _ai_resources
    _ai_runtime = runtime
    _ai_benchmark = ModelBenchmarkSuite(default_runtime=runtime)
    _ai_doctor = AIDoctor(registry=get_ai_registry(), local_runtime=runtime, offline_manager=get_ai_offline())
    _ai_resources = ModelResourceManager(local_runtime=runtime)
    _ai_router = ModelRouter(registry=get_ai_registry(), local_runtime=runtime, offline_mgr=get_ai_offline())


def get_ai_offline() -> OfflineManager:
    global _ai_offline
    if _ai_offline is None:
        _ai_offline = OfflineManager()
    return _ai_offline


def get_ai_router() -> ModelRouter:
    global _ai_router
    if _ai_router is None:
        _ai_router = ModelRouter(
            registry=get_ai_registry(),
            local_runtime=get_ai_runtime(),
            offline_mgr=get_ai_offline(),
        )
    return _ai_router


def get_ai_benchmark() -> ModelBenchmarkSuite:
    global _ai_benchmark
    if _ai_benchmark is None:
        _ai_benchmark = ModelBenchmarkSuite(default_runtime=get_ai_runtime())
    return _ai_benchmark


def get_ai_doctor() -> AIDoctor:
    global _ai_doctor
    if _ai_doctor is None:
        _ai_doctor = AIDoctor(
            registry=get_ai_registry(),
            local_runtime=get_ai_runtime(),
            offline_manager=get_ai_offline(),
        )
    return _ai_doctor


def get_ai_resources() -> ModelResourceManager:
    global _ai_resources
    if _ai_resources is None:
        _ai_resources = ModelResourceManager(local_runtime=get_ai_runtime())
    return _ai_resources


class AIStatusTool(BaseTool):
    name = "ai.status"
    description = "Retrieves live status of AI engines, model routing, local runtimes, hardware profile, and token usage metrics."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, **kwargs: Any) -> ToolResult:
        router = get_ai_router()
        offline = get_ai_offline()
        profiler = HardwareProfiler()
        hw = profiler.detect()
        rt = get_ai_runtime()

        data = {
            "routing_strategy": router.strategy.value,
            "is_online": offline.is_online(),
            "hardware": hw.to_dict(),
            "local_runtime_available": rt.is_runtime_available(),
            "installed_local_models": [m.get("name") for m in rt.list_installed_models()],
            "metrics": router.metrics.to_dict(),
        }
        return ToolResult(success=True, data=data)


class AIRouteTool(BaseTool):
    name = "ai.route"
    description = "Evaluates the optimal engine (deterministic tool, fast intent parser, local model, cloud model) for a given query or task."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        privacy_level: Optional[str] = None,
        prefer_local: Optional[bool] = None,
        **kwargs: Any,
    ) -> ToolResult:
        router = get_ai_router()
        p_level = PrivacyLevel(privacy_level.lower()) if privacy_level else None
        decision = router.route(
            prompt=prompt,
            task_type=task_type,
            explicit_privacy=p_level,
            prefer_local=prefer_local,
        )
        return ToolResult(success=True, data=decision.to_dict())


class AIBenchmarkTool(BaseTool):
    name = "ai.benchmark"
    description = "Executes empirical performance benchmarking on a local model, measuring tokens/sec, TTFT, tool calling, and memory usage."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, model_id: Optional[str] = None, **kwargs: Any) -> ToolResult:
        bench = get_ai_benchmark()
        target_model = model_id or "llama3.1:8b"
        result = await bench.run_benchmark(model_id=target_model)
        return ToolResult(success=True, data=result.to_dict())


class AIDoctorTool(BaseTool):
    name = "ai.doctor"
    description = "Runs comprehensive health diagnostics across hardware, local models, cloud providers, and offline readiness."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, **kwargs: Any) -> ToolResult:
        doc = get_ai_doctor()
        diagnostics = doc.run_diagnostics()
        report_text = doc.format_report(diagnostics)
        return ToolResult(
            success=True,
            data={"diagnostics": diagnostics, "report": report_text},
        )


class AIOfflineTool(BaseTool):
    name = "ai.offline"
    description = "Inspects or toggles offline mode simulation, network reachability, and degraded capability state."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        action: str = "status",
        force_offline: Optional[bool] = None,
        **kwargs: Any,
    ) -> ToolResult:
        offline = get_ai_offline()
        if action == "set" and force_offline is not None:
            offline.set_forced_offline(force_offline)

        capabilities = offline.get_available_capabilities()
        return ToolResult(
            success=True,
            data={
                "is_online": offline.is_online(),
                "forced_offline": offline.is_forced_offline(),
                "available_capabilities": capabilities,
            },
        )


class AIModelsTool(BaseTool):
    name = "ai.models"
    description = "Lists cataloged AI models filtered by provider, capability, or privacy tier."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        provider: Optional[str] = None,
        capability: Optional[str] = None,
        **kwargs: Any,
    ) -> ToolResult:
        reg = get_ai_registry()
        models = reg.list_models()
        if provider:
            p_enum = ProviderType(provider.lower())
            models = [m for m in models if m.provider_type == p_enum]
        if capability:
            models = [m for m in models if capability.lower() in [c.value for c in m.capabilities]]

        return ToolResult(
            success=True,
            data={"models": [m.to_dict() for m in models], "total": len(models)},
        )
