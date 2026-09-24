"""
SHIVANI Security Permissions & Risk Hierarchy Models
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    LOW_RISK = "LOW_RISK"
    SENSITIVE = "SENSITIVE"
    HIGH_RISK = "HIGH_RISK"
    CRITICAL = "CRITICAL"

    @classmethod
    def from_str(cls, val: str) -> "RiskLevel":
        v = val.upper().strip()
        if v in cls.__members__:
            return cls[v]
        if v in ("LOW", "LOWRISK"):
            return cls.LOW_RISK
        if v in ("HIGH", "HIGHRISK"):
            return cls.HIGH_RISK
        return cls.SENSITIVE


class Permission(str, Enum):
    DESKTOP_INPUT = "desktop.input"
    DESKTOP_APP_CONTROL = "desktop.app_control"
    BROWSER_NAVIGATE = "browser.navigate"
    BROWSER_EXTRACT = "browser.extract"
    FILE_READ = "filesystem.read"
    FILE_WRITE = "filesystem.write"
    FILE_DELETE = "filesystem.delete"
    TERMINAL_EXECUTE = "terminal.execute"
    EMAIL_READ = "email.read"
    EMAIL_SEND = "email.send"
    SOCIAL_READ = "social.read"
    SOCIAL_POST = "social.post"
    GITHUB_READ = "github.read"
    GITHUB_WRITE = "github.write"
    PHONE_CONTROL = "phone.control"
    PHONE_READ_MEDIA = "phone.read_media"
    SYSTEM_SECURITY = "system.security"


class PolicyMode(str, Enum):
    LENIENT = "lenient"
    STANDARD = "standard"
    STRICT = "strict"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.SAFE
    description: str = ""
    target: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None
