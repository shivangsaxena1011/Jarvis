"""
SHIVANI Operational Modes: Safe Mode & Demo Mode
Controls system behavior under restricted safety guarantees and non-destructive demonstration conditions.
"""

import os
import logging
from typing import Any, Dict, Optional, Set

from core.errors import SecurityViolation
from security.permissions import RiskLevel

logger = logging.getLogger("shivani.modes")


class SafeModeController:
    """
    Safe Mode restricts SHIVANI execution to read-only or low-risk operations.
    Prevents shell execution, file mutations outside temporary directories,
    and access to sensitive system credentials.
    """

    ALLOWED_RISK_LEVELS: Set[RiskLevel] = {RiskLevel.SAFE, RiskLevel.LOW_RISK}
    BLOCKED_TOOL_PATTERNS: Set[str] = {
        "run_command", "powershell", "cmd", "shell",
        "delete_file", "write_file", "format_drive",
        "device_reboot", "factory_reset"
    }

    def __init__(self, enabled: bool = False):
        # Enable if explicitly requested or via environment
        self._enabled = enabled or (os.getenv("SHIVANI_SAFE_MODE", "0").lower() in ("1", "true", "yes"))

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        logger.warning("SHIVANI Safe Mode ACTIVATED. Destructive operations and shell execution are blocked.")

    def disable(self) -> None:
        self._enabled = False
        logger.info("SHIVANI Safe Mode DEACTIVATED.")

    def validate_tool_execution(self, tool_name: str, risk_level: RiskLevel) -> None:
        """Validates if tool execution is permissible under Safe Mode."""
        if not self._enabled:
            return

        tool_lower = tool_name.lower()
        if any(blocked in tool_lower for blocked in self.BLOCKED_TOOL_PATTERNS):
            raise SecurityViolation(
                f"Tool '{tool_name}' is prohibited while SHIVANI is running in Safe Mode.",
                violation_type="SAFE_MODE_BLOCKED"
            )

        if risk_level not in self.ALLOWED_RISK_LEVELS:
            raise SecurityViolation(
                f"Action '{tool_name}' has risk level {risk_level.value}, which is prohibited in Safe Mode (max allowed: LOW_RISK).",
                violation_type="SAFE_MODE_RISK_EXCEEDED"
            )


class DemoModeController:
    """
    Demo Mode simulates execution of tools without performing real side-effects.
    Used for safe public demonstrations, educational walkthroughs, and UI previews.
    """

    def __init__(self, enabled: bool = False):
        self._enabled = enabled or (os.getenv("SHIVANI_DEMO_MODE", "0").lower() in ("1", "true", "yes"))

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True
        logger.info("SHIVANI Demo Mode ACTIVATED. All external actions will be safely simulated.")

    def disable(self) -> None:
        self._enabled = False
        logger.info("SHIVANI Demo Mode DEACTIVATED.")

    def simulate_execution(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Returns simulated mock result for demonstration purposes."""
        logger.info("[DEMO MODE] Simulating execution of tool '%s' with args %s", tool_name, arguments)
        return {
            "status": "success",
            "demo_simulation": True,
            "tool": tool_name,
            "message": f"[DEMO] Simulated successful execution of '{tool_name}'. No system changes were made."
        }
