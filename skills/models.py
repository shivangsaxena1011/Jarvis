"""
SHIVANI Universal Skills Models
Data models for skill lifecycle states, health statuses, action schemas,
telemetry, and capability descriptors.
"""

from datetime import datetime, timezone
from enum import Enum
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from security.permissions.models import RiskLevel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SkillState(str, Enum):
    DISCOVERED = "DISCOVERED"
    VALIDATING = "VALIDATING"
    INSTALLING = "INSTALLING"
    INSTALLED = "INSTALLED"
    ENABLED = "ENABLED"
    ACTIVE = "ENABLED"
    DISABLED = "DISABLED"
    UPDATING = "UPDATING"
    FAILED = "FAILED"
    UNINSTALLING = "UNINSTALLING"


class SkillHealth(str, Enum):
    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    DISABLED = "DISABLED"
    FAILED = "FAILED"


class ActionVerb(str, Enum):
    DISCOVER = "DISCOVER"
    READ = "READ"
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    EXECUTE = "EXECUTE"
    EXPORT = "EXPORT"
    IMPORT = "IMPORT"
    VERIFY = "VERIFY"


class ActionSchema(BaseModel):
    name: str = Field(..., description="Action identifier (e.g. 'github.create_issue')")
    description: str
    verb: ActionVerb = ActionVerb.EXECUTE
    inputs: Dict[str, Any] = Field(default_factory=dict)
    outputs: Dict[str, Any] = Field(default_factory=dict)
    permissions: List[str] = Field(default_factory=list)
    risk: RiskLevel = RiskLevel.SAFE
    reversible: bool = False
    verification_method: Optional[str] = None


class SkillTelemetry(BaseModel):
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_latency_ms: float = 0.0
    last_latency_ms: float = 0.0
    last_executed: Optional[datetime] = None
    last_error: Optional[str] = None

    @property
    def invocations(self) -> int:
        return self.execution_count

    @invocations.setter
    def invocations(self, value: int) -> None:
        self.execution_count = value

    @property
    def errors(self) -> int:
        return self.failure_count

    @errors.setter
    def errors(self, value: int) -> None:
        self.failure_count = value

    def record_execution(self, success: bool, latency_ms: float, error: Optional[str] = None) -> None:
        self.execution_count += 1
        self.last_latency_ms = latency_ms
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
            self.last_error = error
        self.total_latency_ms += latency_ms
        self.last_executed = utc_now()

    @property
    def success_rate(self) -> float:
        if self.execution_count == 0:
            return 100.0
        return round((self.success_count / self.execution_count) * 100.0, 2)

    @property
    def average_latency_ms(self) -> float:
        if self.execution_count == 0:
            return 0.0
        return round(self.total_latency_ms / self.execution_count, 2)


class SkillMetadata(BaseModel):
    name: str
    display_name: str
    version: str
    author: str = "Community"
    description: str
    category: str = "Productivity"
    capabilities: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.SAFE
    offline_capable: bool = True
    state: SkillState = SkillState.INSTALLED
    health: SkillHealth = SkillHealth.HEALTHY
    installed_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    config_path: Optional[str] = None
    telemetry: SkillTelemetry = Field(default_factory=SkillTelemetry)
