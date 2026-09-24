"""
SHIVANI Observability — Health Check Subsystem
Evaluates component and system operational health.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
import os


class HealthStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    ERROR = "ERROR"


class ComponentHealth:
    def __init__(self, name: str, status: HealthStatus, details: Optional[Dict[str, Any]] = None, message: str = "Operational"):
        self.name = name
        self.status = status
        self.details = details or {}
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
        }


class HealthChecker:
    """Evaluates health across core subsystems."""

    def check_storage(self) -> ComponentHealth:
        try:
            # Check if data directory is writable
            test_path = "data"
            os.makedirs(test_path, exist_ok=True)
            probe_file = os.path.join(test_path, ".health_probe")
            with open(probe_file, "w") as f:
                f.write("ok")
            os.remove(probe_file)
            return ComponentHealth("storage", HealthStatus.ONLINE, {"path": test_path}, "Storage read/write operational")
        except Exception as e:
            return ComponentHealth("storage", HealthStatus.ERROR, {"error": str(e)}, f"Storage inaccessible: {e}")

    def check_security(self) -> ComponentHealth:
        try:
            from security.secret_manager import DPAPIHelper
            # Test DPAPI roundtrip with probe bytes
            probe_bytes = b"probe_secret_val"
            enc = DPAPIHelper.protect(probe_bytes)
            dec = DPAPIHelper.unprotect(enc)
            if dec == probe_bytes:
                return ComponentHealth("security", HealthStatus.ONLINE, {"vault": "encrypted"}, "DPAPI vault operational")
            return ComponentHealth("security", HealthStatus.DEGRADED, {}, "DPAPI returned unexpected value")
        except Exception as e:
            return ComponentHealth("security", HealthStatus.DEGRADED, {"error": str(e)}, f"DPAPI vault issue: {e}")

    def check_tools(self) -> ComponentHealth:
        try:
            from core.orchestrator.orchestrator import Orchestrator
            orch = Orchestrator()
            count = len(orch.tools._tools)
            if count > 0:
                return ComponentHealth("tools", HealthStatus.ONLINE, {"tool_count": count}, f"{count} tools registered")
            return ComponentHealth("tools", HealthStatus.DEGRADED, {"tool_count": 0}, "No tools registered")
        except Exception as e:
            return ComponentHealth("tools", HealthStatus.ERROR, {"error": str(e)}, f"Tool registry error: {e}")

    def check_overall_health(self) -> Dict[str, Any]:
        components = [
            self.check_storage(),
            self.check_security(),
            self.check_tools(),
        ]

        # Determine overall system health
        statuses = [c.status for c in components]
        if any(s == HealthStatus.ERROR for s in statuses):
            overall = HealthStatus.ERROR
        elif any(s == HealthStatus.DEGRADED for s in statuses):
            overall = HealthStatus.DEGRADED
        elif any(s == HealthStatus.AUTH_REQUIRED for s in statuses):
            overall = HealthStatus.AUTH_REQUIRED
        else:
            overall = HealthStatus.ONLINE

        return {
            "overall_status": overall.value,
            "components": {c.name: c.to_dict() for c in components},
        }


HEALTH = HealthChecker()
