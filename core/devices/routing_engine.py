"""Device-Aware Task Routing & Active Device Election Engine for Phase 18.

Evaluates device capabilities, connection states, battery levels, interaction recency,
and task semantics to route tasks to the best-suited device or elect the active primary node.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from core.devices.models import (
    ConnectionState,
    Device,
    DeviceCapability,
    DevicePlatform,
    DeviceTrustState,
)
from core.devices.trust_store import TrustStore

logger = logging.getLogger("shivani.devices.routing")


@dataclass
class RoutingDecision:
    """Detailed result of task routing analysis."""
    selected_device_id: str
    target_platform: str
    confidence_score: float
    reason: str
    ranked_candidates: List[Dict[str, Any]] = field(default_factory=list)


class RoutingEngine:
    """Routes user intents, commands, and tasks across the multi-device mesh."""

    def __init__(self, trust_store: TrustStore, default_primary_device_id: Optional[str] = None):
        self.trust_store = trust_store
        self.active_device_id: Optional[str] = default_primary_device_id
        self._last_interaction_timestamps: Dict[str, float] = {}

    def record_interaction(self, device_id: str) -> None:
        """Record that user interacted with or from a specific device."""
        self._last_interaction_timestamps[device_id] = time.time()
        self.active_device_id = device_id

    def elect_active_device(self) -> Optional[Device]:
        """Elect the current primary active device based on recency, online status, and battery."""
        devices = self.trust_store.list_devices(DeviceTrustState.TRUSTED)
        if not devices:
            return None

        # Filter reachable devices
        online_devices = [d for d in devices if d.is_online(timeout_sec=120.0)]
        if not online_devices:
            # Fall back to any trusted device with latest seen timestamp
            return max(devices, key=lambda d: d.last_seen)

        # Sort by latest interaction or last_seen
        def score_device(d: Device) -> float:
            interaction_time = self._last_interaction_timestamps.get(d.device_id, d.last_seen)
            score = interaction_time
            # Prefer devices that are not critically low on battery
            if d.battery_level is not None and d.battery_level < 15 and not d.is_charging:
                score -= 1000.0
            return score

        best_dev = max(online_devices, key=score_device)
        self.active_device_id = best_dev.device_id
        return best_dev

    def route_task(
        self,
        task_description: str,
        required_capabilities: Optional[List[str | DeviceCapability]] = None,
        preferred_platform: Optional[str | DevicePlatform] = None,
    ) -> RoutingDecision:
        """Route a task to the most appropriate device based on capabilities and context."""
        devices = self.trust_store.list_devices(DeviceTrustState.TRUSTED)
        if not devices:
            raise RuntimeError("No TRUSTED devices found in mesh for task routing.")

        req_caps = [c.value if isinstance(c, DeviceCapability) else c for c in (required_capabilities or [])]
        pref_plat = preferred_platform.value if isinstance(preferred_platform, DevicePlatform) else preferred_platform

        # Infer required capabilities/platform from natural query keywords if not provided
        query = task_description.lower()
        if not req_caps:
            if any(k in query for k in ["take photo", "capture picture", "selfie", "camera"]):
                req_caps.append(DeviceCapability.CAMERA.value)
            elif any(k in query for k in ["call", "dial", "sms", "text message", "whatsapp", "instagram"]):
                req_caps.append(DeviceCapability.UI_AUTOMATION.value)
                if not pref_plat:
                    pref_plat = DevicePlatform.ANDROID.value
            elif any(k in query for k in ["terminal", "powershell", "bash", "compile", "pytest", "vs code", "vscode"]):
                req_caps.append(DeviceCapability.TERMINAL.value)
                if not pref_plat:
                    pref_plat = DevicePlatform.WINDOWS.value
            elif any(k in query for k in ["desktop", "explorer", "organize downloads", "photoshop", "powerpoint"]):
                req_caps.append(DeviceCapability.COMPUTER_CONTROL.value)
                if not pref_plat:
                    pref_plat = DevicePlatform.WINDOWS.value

        scored_candidates: List[Tuple[Device, float, str]] = []

        now = time.time()
        for dev in devices:
            score = 0.0
            reasons = []

            # 1. Capability match (up to 40 pts)
            if req_caps:
                matched_caps = [c for c in req_caps if dev.has_capability(c)]
                match_ratio = len(matched_caps) / len(req_caps)
                score += match_ratio * 40.0
                reasons.append(f"Capabilities matched {len(matched_caps)}/{len(req_caps)}")
                if match_ratio == 0:
                    # Device cannot perform requested actions
                    score -= 50.0
            else:
                score += 20.0  # General task baseline

            # 2. Connection state (up to 25 pts)
            if dev.connection_state == ConnectionState.LOCAL:
                score += 25.0
                reasons.append("Direct local connection")
            elif dev.connection_state == ConnectionState.LAN and dev.is_online():
                score += 20.0
                reasons.append("Active LAN connection")
            elif dev.connection_state == ConnectionState.REMOTE and dev.is_online():
                score += 10.0
                reasons.append("Remote relay connection")
            else:
                score -= 30.0
                reasons.append("Device offline or unresponsive")

            # 3. Battery health (up to 15 pts)
            if dev.is_charging:
                score += 15.0
                reasons.append("Charging")
            elif dev.battery_level is not None:
                if dev.battery_level > 50:
                    score += 12.0
                elif dev.battery_level > 20:
                    score += 6.0
                else:
                    score -= 20.0
                    reasons.append("Battery critically low")
            else:
                score += 10.0  # Desktop mains power assumed

            # 4. Preferred platform (up to 15 pts)
            if pref_plat and dev.platform == pref_plat:
                score += 15.0
                reasons.append(f"Matches preferred platform '{pref_plat}'")

            # 5. Active election & recency (up to 10 pts)
            if dev.device_id == self.active_device_id:
                score += 10.0
                reasons.append("Current active device")
            
            last_touch = self._last_interaction_timestamps.get(dev.device_id, dev.last_seen)
            if (now - last_touch) < 300.0:  # Interacted within 5 minutes
                score += 5.0
                reasons.append("Recently active")

            final_score = max(0.0, score)
            reason_str = "; ".join(reasons)
            scored_candidates.append((dev, final_score, reason_str))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_device, best_score, best_reason = scored_candidates[0]

        ranked = [
            {
                "device_id": d.device_id,
                "display_name": d.display_name,
                "platform": d.platform,
                "score": round(s, 2),
                "reason": r,
            }
            for d, s, r in scored_candidates
        ]

        logger.info(
            f"Routed task '{task_description}' to {best_device.display_name} ({best_device.platform}) "
            f"[score: {best_score:.1f}, reason: {best_reason}]"
        )

        return RoutingDecision(
            selected_device_id=best_device.device_id,
            target_platform=best_device.platform,
            confidence_score=best_score,
            reason=best_reason,
            ranked_candidates=ranked,
        )
