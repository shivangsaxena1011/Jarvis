"""Offline Autonomy, Degraded Mode & Truthful Planning for Phase 19.

Monitors connectivity, manages the offline capability registry, and ensures truthful
degradation without fabricating real-time external data when internet is unavailable.
"""

from __future__ import annotations

import logging
import socket
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger("shivani.ai.offline")

# Registry of capabilities requiring internet access
NETWORK_DEPENDENT_CAPABILITIES: Set[str] = {
    "web_research", "browser_cloud_navigation", "youtube_search",
    "gmail_sync", "linkedin_feed", "github_remote_api", "cloud_llm",
}

# Registry of operations supported 100% offline
OFFLINE_SUPPORTED_OPERATIONS: Set[str] = {
    "computer_control", "window_management", "local_file_system",
    "local_knowledge_search", "local_code_execution", "terminal_operations",
    "local_ocr", "local_vision", "local_audio_stt", "local_audio_tts",
    "device_mesh_local", "task_planning_local", "memory_sqlite",
}


class OfflineManager:
    """Coordinates offline state detection, degraded mode, and truthful execution boundaries."""

    def __init__(self, force_offline: bool = False):
        self._force_offline = force_offline
        self._cached_online_state: Optional[bool] = None
        self._last_check_time: float = 0.0

    def set_force_offline(self, offline: bool) -> None:
        """Manually toggle simulated offline mode for testing or air-gapped environments."""
        self._force_offline = offline
        self._cached_online_state = not offline
        logger.info(f"Force offline mode set to: {offline}")

    def set_forced_offline(self, offline: bool) -> None:
        self.set_force_offline(offline)

    def is_forced_offline(self) -> bool:
        return self._force_offline

    def get_available_capabilities(self) -> Dict[str, str]:
        caps = {
            "computer_control": "Operate Windows windows, controls, mouse, and keyboard",
            "local_file_system": "Inspect, create, edit, search local files and folders",
            "local_knowledge_search": "Search indexed offline Knowledge OS and notes",
            "local_code_execution": "Run code, build, and test locally without internet",
            "terminal_operations": "Execute shell and powershell scripts locally",
            "local_ocr": "Extract text using local OCR (PaddleOCR/Tesseract)",
            "local_vision": "Analyze screen via accessibility tree and local vision",
            "device_mesh_local": "Coordinate and handoff across local Wi-Fi mesh nodes",
            "memory_sqlite": "Access local semantic memory and user preferences",
        }
        if self.is_online():
            caps.update({
                "web_research": "Real-time web queries and browser research",
                "cloud_llm": "Cloud models (Claude 3.5, GPT-4o, Gemini 1.5 Pro)",
                "gmail_sync": "Synchronize and send emails via Gmail",
                "github_remote": "Clone, pull, and push to remote git repositories",
            })
        return caps


    def is_online(self) -> bool:
        """Check real or simulated network connectivity."""
        if self._force_offline:
            return False

        # Fast socket check to public DNS (Cloudflare / Google) with 1s timeout
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.0)
            sock.connect(("1.1.1.1", 53))
            sock.close()
            return True
        except Exception:
            return False

    def validate_capability_offline(self, capability_name: str) -> Tuple[bool, Optional[str]]:
        """Verify whether a specific tool or task capability is supported without internet."""
        if self.is_online():
            return True, None

        cap_lower = capability_name.lower()
        if cap_lower in NETWORK_DEPENDENT_CAPABILITIES or any(k in cap_lower for k in ["web", "youtube", "gmail", "linkedin"]):
            msg = (
                f"Capability '{capability_name}' requires active internet access. "
                "Internet is currently unavailable. Would you like to use local indexed resources instead?"
            )
            return False, msg

        return True, None

    def plan_offline_response(self, task_query: str) -> Optional[str]:
        """Intercept queries requiring live internet when offline, providing honest status."""
        if self.is_online():
            return None

        q_lower = task_query.lower()
        if any(w in q_lower for w in ["latest news", "today's weather", "realtime", "search the web", "search google"]):
            return (
                "Internet access is currently unavailable, so I cannot perform live web research. "
                "I can search your previously indexed local Knowledge OS and documents instead."
            )
        return None
