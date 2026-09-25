"""Model Capability Matrix for Phase 19.

Evaluates discovered model capabilities against task constraints, latency targets,
hardware profiles, and offline requirements without relying on hardcoded assumptions.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Set

from core.ai.models import (
    HardwareProfile,
    ModelCapability,
    ModelDescriptor,
    ModelHealthState,
    ProviderType,
)
from core.ai.registry import ModelRegistry

logger = logging.getLogger("shivani.ai.matrix")


class CapabilityMatrix:
    """Evaluates and matches candidate models against verified requirements."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry

    def find_candidates(
        self,
        required_capabilities: List[ModelCapability | str],
        hardware_profile: Optional[HardwareProfile] = None,
        allow_cloud: bool = True,
        max_latency_ms: Optional[float] = None,
        require_local: bool = False,
    ) -> List[ModelDescriptor]:
        """Find models that satisfy all required capabilities within hardware and latency constraints."""
        all_models = self.registry.list_models()
        req_set = {c.value if isinstance(c, ModelCapability) else c for c in required_capabilities}

        candidates = []
        for m in all_models:
            # Check availability
            if m.health_state in (ModelHealthState.UNAVAILABLE, ModelHealthState.ERROR):
                continue

            # Check cloud restriction
            if not allow_cloud and m.provider_type == ProviderType.CLOUD:
                continue

            if require_local and not m.is_local():
                continue

            # Check latency restriction
            if max_latency_ms is not None and m.latency_ms_p50 > max_latency_ms:
                continue

            # Check hardware constraints for local models
            if m.is_local() and hardware_profile:
                if m.min_ram_gb > hardware_profile.ram_total_gb:
                    continue
                if m.min_vram_gb > 0 and not hardware_profile.has_cuda and m.min_ram_gb > hardware_profile.ram_total_gb:
                    continue


            # Verify capability intersection
            model_caps = set(m.capabilities)
            if req_set.issubset(model_caps):
                candidates.append(m)

        return candidates
