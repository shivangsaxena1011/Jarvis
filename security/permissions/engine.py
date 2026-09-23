"""
SHIVANI Security & Permissions Engine
Implements three-tier risk classification: SAFE, SENSITIVE, CRITICAL.
Manages approval flows, timeouts, and policy enforcement.
"""

from enum import Enum
import uuid
import asyncio
from datetime import datetime, timezone
from typing import Dict, Optional, Any, Callable
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"
    CRITICAL = "CRITICAL"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class ApprovalRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    tool_name: str
    arguments: Dict[str, Any]
    risk_level: RiskLevel
    description: str
    target: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None


class PermissionEngine:
    def __init__(self, policy: str = "strict"):
        self.policy = policy
        # Pending approval requests: request_id -> ApprovalRequest
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        # Completion futures for waiting async tasks: request_id -> asyncio.Future
        self._approval_futures: Dict[str, asyncio.Future] = {}
        # Dynamic tool risk overrides: tool_name -> RiskLevel
        self._tool_risk_overrides: Dict[str, RiskLevel] = {}
        # Pre-approved sessions/tokens
        self._session_preapprovals: set[str] = set()

    def set_tool_risk(self, tool_name: str, risk: RiskLevel) -> None:
        self._tool_risk_overrides[tool_name] = risk

    def get_risk_level(self, tool_name: str, default_risk: RiskLevel = RiskLevel.SAFE) -> RiskLevel:
        return self._tool_risk_overrides.get(tool_name, default_risk)

    def requires_approval(self, risk: RiskLevel) -> bool:
        if self.policy in ("test", "none"):
            return False
        if self.policy == "lenient":
            return risk == RiskLevel.CRITICAL
        elif self.policy == "standard":
            return risk in (RiskLevel.SENSITIVE, RiskLevel.CRITICAL)
        # Strict mode (default)
        return risk in (RiskLevel.SENSITIVE, RiskLevel.CRITICAL)


    async def evaluate_and_request(
        self,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        default_risk: RiskLevel,
        description: str,
        target: str = "",
        timeout_seconds: float = 120.0
    ) -> bool:
        """
        Evaluates risk for the tool invocation. If approval is required, creates an approval
        request and suspends execution until the user approves, rejects, or times out.
        Returns True if authorized, False otherwise.
        """
        risk = self.get_risk_level(tool_name, default_risk)
        
        # Safe operations never require explicit confirmation
        if not self.requires_approval(risk):
            return True

        # Check session preapprovals (e.g., user approved entire batch)
        approval_key = f"{task_id}:{tool_name}"
        if approval_key in self._session_preapprovals:
            return True

        # Create approval request
        req = ApprovalRequest(
            task_id=task_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk,
            description=description,
            target=target
        )
        self._pending_requests[req.id] = req
        
        loop = asyncio.get_running_loop()
        future: asyncio.Future = loop.create_future()
        self._approval_futures[req.id] = future

        try:
            # Wait for user resolution via UI / voice / API
            approved = await asyncio.wait_for(future, timeout=timeout_seconds)
            return bool(approved)
        except asyncio.TimeoutError:
            req.status = ApprovalStatus.EXPIRED
            req.resolved_at = datetime.now(timezone.utc).isoformat()
            return False
        finally:
            self._approval_futures.pop(req.id, None)

    def resolve_request(self, request_id: str, approved: bool, resolved_by: str = "user") -> bool:
        """Called when user approves or rejects an action via UI or Voice."""
        req = self._pending_requests.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return False

        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.resolved_at = datetime.now(timezone.utc).isoformat()
        req.resolved_by = resolved_by

        future = self._approval_futures.get(request_id)
        if future and not future.done():
            future.set_result(approved)
        return True

    def list_pending_requests(self) -> list[ApprovalRequest]:
        return [r for r in self._pending_requests.values() if r.status == ApprovalStatus.PENDING]

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._pending_requests.get(request_id)
