"""
SHIVANI Multi-Agent Communication Protocol
Defines structured message envelopes and standardized execution output contracts
for transparent, audit-ready inter-agent collaboration.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid
from pydantic import BaseModel, Field


class AgentMessageType(str, Enum):
    REQUEST = "request"
    RESPONSE = "response"
    STATUS_UPDATE = "status_update"
    HANDOFF = "handoff"
    ERROR = "error"


class AgentMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message_type: AgentMessageType = AgentMessageType.REQUEST
    payload: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentResponse(BaseModel):
    status: str # "success" | "failed" | "waiting_approval" | "partial"
    summary: str
    artifacts: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def success(cls, summary: str, artifacts: Optional[List[str]] = None, data: Optional[Dict[str, Any]] = None) -> "AgentResponse":
        return cls(
            status="success",
            summary=summary,
            artifacts=artifacts or [],
            data=data or {},
        )

    @classmethod
    def failed(cls, summary: str, errors: Optional[List[str]] = None) -> "AgentResponse":
        return cls(
            status="failed",
            summary=summary,
            errors=errors or [summary],
        )
