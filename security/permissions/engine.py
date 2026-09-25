"""
SHIVANI Security & Permissions Engine
Implements three-tier risk classification: SAFE, SENSITIVE, CRITICAL.
Manages approval flows, timeouts, and policy enforcement.
"""

from enum import Enum
import uuid
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any, Callable, List
from pydantic import BaseModel, Field


from security.permissions.models import (
    RiskLevel,
    ApprovalStatus,
    ApprovalScope,
    ScopedPreapproval,
    ApprovalRequest,
)


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
        # Scoped preapprovals: "task_id:tool_name" -> List[ScopedPreapproval]
        self._scoped_preapprovals: Dict[str, List[ScopedPreapproval]] = {}

    def grant_preapproval(
        self,
        task_id: str,
        tool_name: str,
        scope: ApprovalScope = ApprovalScope.ONE_ACTION,
        duration_seconds: Optional[float] = None,
        max_invocations: Optional[int] = None,
    ) -> ScopedPreapproval:
        """Preapproves a specific tool execution within a task/workflow with scope and expiration."""
        approval_key = f"{task_id}:{tool_name}"
        self._session_preapprovals.add(approval_key)

        expires_at = None
        if duration_seconds is not None:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=duration_seconds)).isoformat()
        elif scope == ApprovalScope.TIME_LIMITED:
            expires_at = (datetime.now(timezone.utc) + timedelta(seconds=300.0)).isoformat()

        if max_invocations is None:
            if scope == ApprovalScope.ONE_ACTION:
                max_invocations = 1
            else:
                max_invocations = None

        preapproval = ScopedPreapproval(
            task_id=task_id,
            tool_name=tool_name,
            scope=scope,
            expires_at=expires_at,
            max_invocations=max_invocations,
        )
        if approval_key not in self._scoped_preapprovals:
            self._scoped_preapprovals[approval_key] = []
        self._scoped_preapprovals[approval_key].append(preapproval)
        return preapproval

    def check_and_consume_preapproval(self, task_id: str, tool_name: str) -> bool:
        """Checks if a valid preapproval exists and consumes an invocation."""
        approval_key = f"{task_id}:{tool_name}"
        if approval_key in self._scoped_preapprovals:
            now = datetime.now(timezone.utc)
            valid_list = [p for p in self._scoped_preapprovals[approval_key] if p.is_valid(now)]
            if valid_list:
                active = valid_list[0]
                active.consume()
                if not active.is_valid(now):
                    valid_list.remove(active)
                self._scoped_preapprovals[approval_key] = valid_list
                if not valid_list:
                    self._session_preapprovals.discard(approval_key)
                return True
            else:
                self._scoped_preapprovals.pop(approval_key, None)
                self._session_preapprovals.discard(approval_key)

        if approval_key in self._session_preapprovals:
            return True
        return False

    def revoke_preapproval(self, task_id: str, tool_name: str) -> None:
        """Revokes a session preapproval."""
        approval_key = f"{task_id}:{tool_name}"
        self._session_preapprovals.discard(approval_key)
        self._scoped_preapprovals.pop(approval_key, None)

    def revoke_task_preapprovals(self, task_id: str) -> None:
        """Revokes all preapprovals associated with a given task."""
        prefix = f"{task_id}:"
        keys_to_remove = [k for k in self._scoped_preapprovals if k.startswith(prefix)]
        for k in keys_to_remove:
            self._scoped_preapprovals.pop(k, None)
            self._session_preapprovals.discard(k)
        legacy_keys = [k for k in self._session_preapprovals if k.startswith(prefix)]
        for k in legacy_keys:
            self._session_preapprovals.discard(k)

    def set_tool_risk(self, tool_name: str, risk: RiskLevel) -> None:
        self._tool_risk_overrides[tool_name] = risk

    def get_risk_level(self, tool_name: str, default_risk: RiskLevel = RiskLevel.SAFE) -> RiskLevel:
        return self._tool_risk_overrides.get(tool_name, default_risk)

    def requires_approval(self, risk: RiskLevel) -> bool:
        if self.policy in ("test", "none"):
            return False
        if self.policy == "lenient":
            return risk in (RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)
        elif self.policy == "standard":
            return risk in (RiskLevel.SENSITIVE, RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)
        # Strict mode (default)
        return risk in (RiskLevel.SENSITIVE, RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)



    def request_approval(
        self,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        description: str,
        risk_level: RiskLevel,
        target: str = ""
    ) -> ApprovalRequest:
        """Creates a pending approval request without blocking."""
        req = ApprovalRequest(
            task_id=task_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
            description=description,
            target=target
        )
        self._pending_requests[req.id] = req
        return req

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

        # Check session / scoped preapprovals (e.g., user approved batch or single action)
        if self.check_and_consume_preapproval(task_id, tool_name):
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
