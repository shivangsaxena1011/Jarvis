"""AI Doctor Diagnostic Engine for Phase 19.

Comprehensive health, hardware, local runtime, cloud credentials, and offline
autonomy diagnostic engine for Shivani AI.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from core.ai.hardware import HardwareProfiler
from core.ai.local_runtime import LocalModelRuntime, OllamaLocalRuntime
from core.ai.offline import OfflineManager
from core.ai.registry import ModelRegistry

logger = logging.getLogger("shivani.ai.doctor")


class AIDoctor:
    """Diagnoses AI subsystems, hardware profiles, model installations, and offline readiness."""

    RECOMMENDED_LOCAL_MODELS = [
        ("llama3.1:8b", "General desktop reasoning, tool planning, and private summarization"),
        ("qwen2.5-coder:7b", "Local code synthesis, bug fixing, and script execution"),
        ("phi3:mini", "Ultra-fast lightweight intent extraction and low-RAM fallback"),
    ]

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        local_runtime: Optional[LocalModelRuntime] = None,
        offline_manager: Optional[OfflineManager] = None,
    ):
        self.registry = registry or ModelRegistry()
        self.runtime = local_runtime or OllamaLocalRuntime()
        self.offline_manager = offline_manager or OfflineManager()
        self.profiler = HardwareProfiler()

    def run_diagnostics(self) -> Dict[str, Any]:
        """Perform comprehensive system diagnostics across all AI subsystems."""
        checks = {}
        warnings: List[str] = []
        errors: List[str] = []
        recommendations: List[str] = []

        # 1. Hardware checks
        hw = self.profiler.detect()
        hw_ok = hw.total_ram_gb >= 7.5
        checks["hardware"] = {
            "status": "PASS" if hw_ok else "WARN",
            "cpu_cores": hw.cpu_cores,
            "total_ram_gb": hw.total_ram_gb,
            "available_ram_gb": hw.available_ram_gb,
            "gpu_vendor": hw.gpu_vendor,
            "gpu_name": hw.gpu_name,
            "gpu_vram_gb": hw.gpu_vram_gb,
            "has_accelerator": hw.has_accelerator,
        }
        if not hw_ok:
            warnings.append(f"Host has {hw.total_ram_gb} GB RAM. 8 GB+ is recommended for 7B/8B local models.")
            recommendations.append("Consider running lightweight 3B/4B quantized models (e.g. phi3:mini).")

        # 2. Local Runtime check
        rt_available = self.runtime.is_runtime_available()
        installed_models = self.runtime.list_installed_models() if rt_available else []
        installed_names = [m.get("name", "").split(":")[0] for m in installed_models]
        installed_full = [m.get("name", "") for m in installed_models]

        checks["local_runtime"] = {
            "status": "PASS" if rt_available else "WARN",
            "available": rt_available,
            "installed_models_count": len(installed_models),
            "installed_models": installed_full,
        }
        if not rt_available:
            warnings.append("Local runtime (Ollama/llama.cpp) is not responding on standard ports.")
            recommendations.append("Install and start Ollama (https://ollama.com) to enable offline private intelligence.")
        else:
            # Check recommended models
            missing = []
            for rec, desc in self.RECOMMENDED_LOCAL_MODELS:
                base_rec = rec.split(":")[0]
                if base_rec not in installed_names and rec not in installed_full:
                    missing.append((rec, desc))
            if missing:
                for rec, desc in missing:
                    recommendations.append(f"Run 'ollama pull {rec}' ({desc}) to expand local capabilities.")

        # 3. Cloud Provider & API Keys check
        cloud_providers = {
            "OPENAI_API_KEY": bool(os.getenv("OPENAI_API_KEY")),
            "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
            "GEMINI_API_KEY": bool(os.getenv("GEMINI_API_KEY")),
            "GROQ_API_KEY": bool(os.getenv("GROQ_API_KEY")),
        }
        has_any_cloud = any(cloud_providers.values())
        checks["cloud_providers"] = {
            "status": "PASS" if has_any_cloud else "WARN",
            "keys_detected": {k: "CONFIGURED" if v else "MISSING" for k, v in cloud_providers.items()},
        }
        if not has_any_cloud:
            warnings.append("No cloud API keys detected (OpenAI, Anthropic, Gemini, Groq). Cloud fallback is disabled.")
            recommendations.append("Add OPENAI_API_KEY or GROQ_API_KEY to .env for high-complexity reasoning tasks.")

        # 4. Network and Offline Readiness
        network_online = self.offline_manager.is_online()
        has_offline_reasoning = len(installed_models) > 0 or rt_available
        checks["offline_readiness"] = {
            "status": "PASS" if has_offline_reasoning else "WARN",
            "network_online": network_online,
            "offline_reasoning_capable": has_offline_reasoning,
        }
        if not network_online and not has_offline_reasoning:
            errors.append("Host is currently OFFLINE and no local LLM runtime is available. Assistant running on deterministic rule engine only.")
            recommendations.append("Configure a local model before traveling or disconnecting from internet.")

        # Overall Status
        if errors:
            overall = "DEGRADED"
        elif warnings:
            overall = "HEALTHY_WITH_WARNINGS"
        else:
            overall = "OPTIMAL"

        return {
            "overall_status": overall,
            "checks": checks,
            "errors": errors,
            "warnings": warnings,
            "recommendations": recommendations,
        }

    def format_report(self, diagnostics: Optional[Dict[str, Any]] = None) -> str:
        """Render diagnostic results into human-readable terminal/log report."""
        d = diagnostics or self.run_diagnostics()
        lines = [
            "============================================================",
            f"  SHIVANI AI DOCTOR DIAGNOSTIC REPORT — STATUS: {d['overall_status']}",
            "============================================================",
            "",
            "1. HARDWARE & ACCELERATION:",
        ]
        hw = d["checks"]["hardware"]
        lines.append(f"   - CPU Cores: {hw['cpu_cores']} | RAM: {hw['available_ram_gb']} / {hw['total_ram_gb']} GB")
        lines.append(f"   - GPU: {hw['gpu_name']} ({hw['gpu_vendor']}) | VRAM: {hw['gpu_vram_gb']} GB | Accelerator: {hw['has_accelerator']}")
        lines.append(f"   - Check: {hw['status']}")
        lines.append("")

        lines.append("2. LOCAL RUNTIME & MODELS:")
        rt = d["checks"]["local_runtime"]
        lines.append(f"   - Daemon Available: {rt['available']}")
        lines.append(f"   - Models Installed ({rt['installed_models_count']}): {', '.join(rt['installed_models']) or 'None'}")
        lines.append(f"   - Check: {rt['status']}")
        lines.append("")

        lines.append("3. CLOUD PROVIDERS & CREDENTIALS:")
        cp = d["checks"]["cloud_providers"]
        for k, v in cp["keys_detected"].items():
            lines.append(f"   - {k}: {v}")
        lines.append(f"   - Check: {cp['status']}")
        lines.append("")

        lines.append("4. OFFLINE READINESS:")
        off = d["checks"]["offline_readiness"]
        lines.append(f"   - Network Reachable: {off['network_online']}")
        lines.append(f"   - Local LLM Autonomous: {off['offline_reasoning_capable']}")
        lines.append(f"   - Check: {off['status']}")
        lines.append("")

        if d["errors"]:
            lines.append("CRITICAL ISSUES:")
            for e in d["errors"]:
                lines.append(f"   [!] {e}")
            lines.append("")

        if d["warnings"]:
            lines.append("WARNINGS:")
            for w in d["warnings"]:
                lines.append(f"   [*] {w}")
            lines.append("")

        if d["recommendations"]:
            lines.append("RECOMMENDED ACTIONS:")
            for idx, r in enumerate(d["recommendations"], 1):
                lines.append(f"   {idx}. {r}")
            lines.append("")

        lines.append("============================================================")
        return "\n".join(lines)
