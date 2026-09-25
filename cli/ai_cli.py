"""CLI command handler for Phase 19: Local AI, Model Routing & Offline Autonomy.

Provides direct command-line control over AI routing, hardware profiling,
local model benchmarking, AI Doctor diagnostics, and offline autonomy controls.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

from core.ai.benchmark import ModelBenchmarkSuite
from core.ai.doctor import AIDoctor
from core.ai.hardware import HardwareProfiler
from core.ai.models import PrivacyLevel, ProviderType, RoutingStrategy
from core.ai.offline import OfflineManager
from core.ai.registry import ModelRegistry
from core.ai.router import ModelRouter
from tools.ai.ai_tools import get_ai_benchmark, get_ai_doctor, get_ai_offline, get_ai_router, get_ai_runtime


def run_ai_status() -> int:
    router = get_ai_router()
    offline = get_ai_offline()
    profiler = HardwareProfiler()
    hw = profiler.detect()
    rt = get_ai_runtime()
    metrics = router.metrics

    print("\n=== SHIVANI AI SUBSYSTEM STATUS ===")
    print(f"Routing Strategy        : {router.strategy.value.upper()}")
    print(f"Network Connectivity    : {'ONLINE' if offline.is_online() else 'OFFLINE (Degraded)'}")
    print(f"Forced Offline Override : {offline.is_forced_offline()}")
    print(f"Local Runtime (Ollama)  : {'ACTIVE' if rt.is_runtime_available() else 'UNAVAILABLE'}")
    installed = [m.get("name") for m in rt.list_installed_models()]
    print(f"Installed Local Models  : {', '.join(installed) if installed else 'None'}")
    print(f"\n--- Host Hardware Profile ---")
    print(f"CPU Cores               : {hw.cpu_cores}")
    print(f"System RAM              : {hw.available_ram_gb:.1f} GB free / {hw.total_ram_gb:.1f} GB total")
    print(f"GPU & Accelerator       : {hw.gpu_name} ({hw.gpu_vendor}) | VRAM: {hw.gpu_vram_gb:.1f} GB")
    print(f"Recommended Model Tier  : {hw.recommended_local_size}")
    print(f"\n--- Live AI Usage Metrics ---")
    print(f"Total Requests Processed: {metrics.total_requests} (Local: {metrics.local_requests}, Cloud: {metrics.cloud_requests}, Fast-Path: {metrics.deterministic_requests})")
    print(f"Tokens (In / Out)       : {metrics.total_input_tokens} / {metrics.total_output_tokens}")
    print(f"Estimated Cost (USD)    : ${metrics.estimated_cost_usd:.4f}")
    print(f"Average Latency         : {metrics.average_latency_ms} ms\n")
    return 0


def run_ai_models(provider: Optional[str] = None, capability: Optional[str] = None) -> int:
    reg = ModelRegistry()
    models = reg.list_models()
    if provider:
        p_enum = ProviderType(provider.lower())
        models = [m for m in models if m.provider_type == p_enum]
    if capability:
        models = [m for m in models if capability.lower() in [c.value for c in m.capabilities]]

    print("\n=== SHIVANI MODEL CATALOG ===")
    print(f"Total Models Cataloged: {len(models)}\n")
    print(f"{'MODEL ID':<22} {'PROVIDER':<15} {'SPEED (t/s)':<12} {'CTX (k)':<10} {'MIN RAM':<10} {'HEALTH':<10}")
    print("-" * 80)
    for m in models:
        speed = f"{m.speed_tokens_per_sec:.0f}"
        ctx = f"{m.context_window // 1024}k"
        ram = f"{m.min_ram_gb:.1f}G" if m.min_ram_gb else "-"
        print(f"{m.model_id:<22} {m.provider_type.value:<15} {speed:<12} {ctx:<10} {ram:<10} {m.health_state.value:<10}")
    print()
    return 0


def run_ai_route(
    query: str,
    privacy: Optional[str] = None,
    prefer_local: bool = False,
    strategy: Optional[str] = None,
) -> int:
    router = get_ai_router()
    p_level = PrivacyLevel(privacy.lower()) if privacy else None
    strat = RoutingStrategy(strategy.lower()) if strategy else None

    decision = router.route(
        prompt=query,
        explicit_privacy=p_level,
        strategy_override=strat,
        prefer_local=prefer_local,
    )

    print("\n=== SHIVANI AI ROUTING EVALUATION ===")
    print(f"Input Query        : \"{query}\"")
    print(f"Selected Model     : {decision.selected_model_id} ({decision.provider_type.value})")
    print(f"Fallback Model     : {decision.fallback_model_id or 'None'}")
    print(f"Is Fast Path / Det : {decision.is_deterministic}")
    print(f"Privacy Tier       : {decision.privacy_level.value}")
    print(f"Confidence Score   : {decision.confidence_score * 100:.0f}%")
    print(f"Applied Policies   : {', '.join(decision.applied_policies)}")
    print(f"Routing Reason     : {decision.reason}\n")
    return 0


def run_ai_benchmark(model_id: Optional[str] = None) -> int:
    bench = get_ai_benchmark()
    target = model_id or "llama3.1:8b"
    print(f"\nRunning empirical benchmark on model: {target} ...")
    res = asyncio.run(bench.run_benchmark(model_id=target))

    print("\n=== MODEL BENCHMARK RESULTS ===")
    print(f"Model ID            : {res.model_id}")
    print(f"Tokens Per Second   : {res.tokens_per_second:.1f} t/s")
    print(f"Time to First Token : {res.latency_first_token_ms:.1f} ms")
    print(f"Total Benchmark Time: {res.total_time_ms:.1f} ms")
    print(f"Tool Calling Test   : {'PASSED' if res.tool_calling_passed else 'FAILED'}")
    print(f"JSON Structured Out : {'PASSED' if res.structured_output_passed else 'FAILED'}")
    print(f"Estimated Memory    : {res.memory_used_mb:.0f} MB RAM / {res.vram_used_mb:.0f} MB VRAM\n")
    return 0


def run_ai_doctor() -> int:
    doc = get_ai_doctor()
    print(doc.format_report())
    return 0


def run_ai_offline(action: str = "status", force: Optional[bool] = None) -> int:
    offline = get_ai_offline()
    if force is not None:
        offline.set_forced_offline(force)

    print("\n=== SHIVANI OFFLINE AUTONOMY ===")
    print(f"Network Reachability : {'CONNECTED' if offline.is_online() else 'DISCONNECTED'}")
    print(f"Forced Offline Flag  : {offline.is_forced_offline()}")
    print("\nAvailable Offline Capabilities:")
    for cap, desc in offline.get_available_capabilities().items():
        print(f"  [+] {cap:<25}: {desc}")
    print()
    return 0


def handle_ai_cli(args: argparse.Namespace) -> int:
    action = getattr(args, "ai_action", "status") or "status"
    if action == "status":
        return run_ai_status()
    elif action == "models":
        return run_ai_models(provider=args.provider, capability=args.capability)
    elif action == "route":
        return run_ai_route(
            query=args.query,
            privacy=args.privacy,
            prefer_local=args.local,
            strategy=args.strategy,
        )
    elif action == "benchmark":
        return run_ai_benchmark(model_id=args.model)
    elif action == "doctor":
        return run_ai_doctor()
    elif action == "offline":
        force_val = None
        if getattr(args, "force", False):
            force_val = True
        elif getattr(args, "online", False):
            force_val = False
        return run_ai_offline(action=args.ai_action, force=force_val)
    else:
        print(f"Unknown AI action: {action}")
        return 1
