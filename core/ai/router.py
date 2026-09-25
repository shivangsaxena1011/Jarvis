"""Intelligent Model Router for Phase 19.

Evaluates task complexity, privacy sensitivity, latency requirements, hardware resources,
and user preferences to route to the smallest reliable capability (deterministic, local, specialized, or cloud).
"""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from core.ai.hardware import detect_hardware
from core.ai.matrix import CapabilityMatrix
from core.ai.models import (
    AIUsageMetrics,
    HardwareProfile,
    ModelCapability,
    ModelDescriptor,
    ModelHealthState,
    PrivacyLevel,
    ProviderType,
    RoutingDecision,
    RoutingStrategy,
)
from core.ai.privacy import DataClassifier
from core.ai.registry import ModelRegistry

logger = logging.getLogger("shivani.ai.router")

# Regex to detect simple math queries for deterministic calculator fast path
MATH_PATTERN = re.compile(r"^\s*(?:what is|calculate|compute)?\s*([\d\.\s\+\-\*\/\(\)\^\%]+)\??\s*$", re.IGNORECASE)

# Simple desktop commands for fast intent routing
FAST_COMMAND_KEYWORDS = [
    "open chrome", "open vs code", "open notepad", "open terminal",
    "close chrome", "close notepad", "close window",
    "minimize", "maximize", "take screenshot", "screenshot",
    "pause music", "stop shivani", "show tasks", "open settings"
]


class ModelRouter:
    """Intelligently routes requests to the optimal engine or deterministic fast path."""

    def __init__(
        self,
        registry: Optional[ModelRegistry] = None,
        hardware_profile: Optional[HardwareProfile] = None,
        default_strategy: RoutingStrategy = RoutingStrategy.AUTO,
        local_runtime: Optional[Any] = None,
        offline_mgr: Optional[Any] = None,
    ):
        self.registry = registry or ModelRegistry()
        self.hardware = hardware_profile or detect_hardware()
        self.matrix = CapabilityMatrix(registry=self.registry)
        self.strategy = default_strategy
        self.local_runtime = local_runtime
        self.offline_mgr = offline_mgr
        self.allow_cloud = True
        self.metrics = AIUsageMetrics()

    def set_strategy(self, strategy: RoutingStrategy | str) -> None:
        self.strategy = RoutingStrategy(strategy) if isinstance(strategy, str) else strategy
        logger.info(f"Updated model routing strategy to: {self.strategy.value}")

    def route(
        self,
        task_query: Optional[str] = None,
        prompt: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        required_capabilities: Optional[List[ModelCapability | str]] = None,
        privacy_override: Optional[PrivacyLevel] = None,
        explicit_privacy: Optional[PrivacyLevel] = None,
        strategy_override: Optional[RoutingStrategy] = None,
        prefer_local: Optional[bool] = None,
        task_type: Optional[str] = None,
    ) -> RoutingDecision:
        """Analyze query and select the optimal model with an ordered fallback chain."""
        effective_query = (prompt or task_query or "").strip()
        strategy = strategy_override or self.strategy
        if prefer_local:
            strategy = RoutingStrategy.LOCAL_FIRST
        effective_privacy = privacy_override or explicit_privacy


        # 1. FAST PATH 1: Deterministic Math Calculator
        math_match = MATH_PATTERN.match(effective_query)
        if math_match:
            expr = math_match.group(1).strip()
            # Ensure it actually has numbers and an operator
            if any(op in expr for op in ["+", "-", "*", "/", "^", "%"]) and any(c.isdigit() for c in expr):
                return RoutingDecision(
                    task_type="arithmetic",
                    selected_model_id="deterministic-calc",
                    fallback_model_id="phi3:mini",
                    provider_type=ProviderType.DETERMINISTIC,
                    is_deterministic=True,
                    confidence_score=1.0,
                    reason="Routed to deterministic math engine for exact arithmetic evaluation.",
                    privacy_level=PrivacyLevel.PUBLIC,
                    applied_policies=["deterministic_fast_path"],
                    constraints={"expression": expr},
                )

        # 2. FAST PATH 2: Fast Regex & Rule Intent Classifier for simple OS commands
        q_lower = effective_query.lower()
        if any(cmd in q_lower for cmd in FAST_COMMAND_KEYWORDS):
            return RoutingDecision(
                task_type="desktop_command",
                selected_model_id="fast-intent-parser",
                fallback_model_id="phi3:mini",
                provider_type=ProviderType.DETERMINISTIC,
                is_deterministic=True,
                confidence_score=0.95,
                reason="Direct fast path intent routing for unambiguous desktop command.",
                privacy_level=PrivacyLevel.PUBLIC,
                applied_policies=["intent_fast_path"],
            )

        # 3. Privacy Classification
        if effective_privacy:
            privacy_level = effective_privacy
            privacy_reasons = ["Explicit privacy override provided."]
        else:
            privacy_level, privacy_reasons = DataClassifier.classify(effective_query, metadata=context)

        # 4. Determine Capability Requirements
        req_caps = list(required_capabilities or [])
        if not req_caps:
            # Infer capabilities from text
            if any(k in q_lower for k in ["def ", "class ", "function", "bug", "code", "refactor", "pytest", "compile"]):
                req_caps.append(ModelCapability.CODING.value)
            elif any(k in q_lower for k in ["summarize", "research", "paper", "analyze document", "synthesis"]):
                req_caps.append(ModelCapability.RESEARCH_SYNTHESIS.value)
            elif any(k in q_lower for k in ["plan", "workflow", "organize", "execute"]):
                req_caps.append(ModelCapability.PLANNING.value)
            else:
                req_caps.append(ModelCapability.SIMPLE_CONVERSATION.value)

        # 5. Evaluate Cloud Permissions
        # CRITICAL/SENSITIVE privacy -> cloud strictly barred
        # PRIVACY_FIRST strategy -> cloud barred
        # Offline -> cloud barred
        allow_cloud = self.allow_cloud and (privacy_level not in (PrivacyLevel.CRITICAL, PrivacyLevel.SENSITIVE))
        if strategy == RoutingStrategy.PRIVACY_FIRST:
            allow_cloud = False
        if self.offline_mgr and not self.offline_mgr.is_online():
            allow_cloud = False


        # 6. Find Eligible Candidates
        candidates = self.matrix.find_candidates(
            required_capabilities=req_caps,
            hardware_profile=self.hardware,
            allow_cloud=allow_cloud,
            require_local=(privacy_level == PrivacyLevel.CRITICAL),
        )

        if not candidates:
            # Fallback to general local model if available or small local
            candidates = self.registry.list_models(provider_type=ProviderType.LOCAL)
            if not candidates:
                # Absolute failsafe
                candidates = [self.registry.get_model("fast-intent-parser")]

        # 7. Score Candidates
        scored: List[Tuple[ModelDescriptor, float, str]] = []
        for m in candidates:
            score = 0.0
            reasons = []

            # A. Capability strength
            score += (m.reasoning_score * 30.0)
            if ModelCapability.CODING.value in req_caps:
                score += (m.coding_score * 20.0)

            # B. Strategy affinity
            if strategy == RoutingStrategy.LOCAL_FIRST and m.is_local():
                score += 40.0
                reasons.append("Prefers local model")
            elif strategy == RoutingStrategy.CLOUD_FIRST and m.provider_type == ProviderType.CLOUD:

                score += 25.0
                reasons.append("Prefers cloud model")
            elif strategy == RoutingStrategy.SPEED_FIRST:
                score += min(30.0, (m.speed_tokens_per_sec / 3.0))
                reasons.append(f"Fast response ({m.speed_tokens_per_sec} t/s)")
            elif strategy == RoutingStrategy.COST_AWARE:
                if m.is_local():
                    score += 30.0
                    reasons.append("Zero marginal API cost")
                else:
                    score -= (m.cost_per_1k_input * 1000.0)

            # C. Privacy affinity
            if privacy_level in (PrivacyLevel.PRIVATE, PrivacyLevel.SENSITIVE) and m.is_local():
                score += 30.0
                reasons.append(f"Enforces local privacy tier ({privacy_level.value})")

            scored.append((m, score, "; ".join(reasons)))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_model, best_score, rationale = scored[0]

        # Determine fallback model
        fallback_model_id = None
        for cand, _, _ in scored[1:]:
            if cand.model_id != best_model.model_id:
                fallback_model_id = cand.model_id
                break
        if not fallback_model_id:
            fallback_model_id = "phi3:mini" if best_model.model_id != "phi3:mini" else "fast-intent-parser"

        decision = RoutingDecision(
            task_type="reasoning_task",
            selected_model_id=best_model.model_id,
            fallback_model_id=fallback_model_id,
            provider_type=best_model.provider_type,
            is_deterministic=False,
            confidence_score=min(1.0, max(0.5, best_score / 100.0)),
            reason=f"Selected {best_model.name} based on capabilities ({', '.join(req_caps)}) and {privacy_level.value} privacy.",
            privacy_level=privacy_level,
            applied_policies=[strategy.value, f"privacy_{privacy_level.value}"],
            constraints={
                "strategy": strategy.value,
                "allow_cloud": allow_cloud,
                "required_capabilities": req_caps,
                "privacy_reasons": privacy_reasons,
            },
        )

        logger.info(
            f"Routed query '{effective_query[:35]}' -> {best_model.model_id} ({best_model.provider_type.value}) "
            f"[Fallback: {fallback_model_id}]"
        )
        return decision
