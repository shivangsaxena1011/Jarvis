"""
SHIVANI Dynamic Policy Engine
Evaluates 5-tier risk levels against policy modes (STRICT, STANDARD, LENIENT),
coordinates user approval requests, manages preapprovals, and enforces timeouts.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Set
import uuid

from security.permissions import (
    ApprovalRequest,
    ApprovalStatus,
    PolicyMode,
    RiskLevel,
)


class PolicyEngine:
    def __init__(self, policy: str = "strict"):
        if isinstance(policy, PolicyMode):
            self.policy = policy
        else:
            p_clean = str(policy).lower().strip()
            self.policy = PolicyMode(p_clean) if p_clean in [m.value for m in PolicyMode] else PolicyMode.STRICT

        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._approval_futures: Dict[str, asyncio.Future] = {}
        self._tool_risk_overrides: Dict[str, RiskLevel] = {}
        self._session_preapprovals: Set[str] = set()

    def set_tool_override(self, tool_name: str, risk: RiskLevel) -> None:
        self._tool_risk_overrides[tool_name] = risk

    def get_tool_risk(self, tool_name: str, default_risk: RiskLevel = RiskLevel.SAFE) -> RiskLevel:
        return self._tool_risk_overrides.get(tool_name, default_risk)

    def grant_preapproval(self, task_id: str, tool_name: str) -> None:
        self._session_preapprovals.add(f"{task_id}:{tool_name}")

    def revoke_preapproval(self, task_id: str, tool_name: str) -> None:
        self._session_preapprovals.discard(f"{task_id}:{tool_name}")

    def requires_approval(self, risk: RiskLevel, task_id: Optional[str] = None, tool_name: Optional[str] = None) -> bool:
        """Determines if action requires explicit confirmation based on policy mode and risk tier."""
        if task_id and tool_name and f"{task_id}:{tool_name}" in self._session_preapprovals:
            return False

        if self.policy == PolicyMode.LENIENT:
            return risk in (RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)
        elif self.policy == PolicyMode.STANDARD:
            return risk in (RiskLevel.SENSITIVE, RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)
        else: # STRICT
            return risk != RiskLevel.SAFE

    def create_request(
        self,
        task_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        risk_level: RiskLevel,
        description: str,
        target: str = "",
    ) -> ApprovalRequest:
        req = ApprovalRequest(
            task_id=task_id,
            tool_name=tool_name,
            arguments=arguments,
            risk_level=risk_level,
            description=description,
            target=target,
        )
        self._pending_requests[req.id] = req
        return req

    async def wait_for_approval(self, request_id: str, timeout: float = 60.0) -> bool:
        req = self._pending_requests.get(request_id)
        if not req:
            return False

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._approval_futures[request_id] = future

        try:
            approved = await asyncio.wait_for(future, timeout=timeout)
            return approved
        except asyncio.TimeoutError:
            req.status = ApprovalStatus.EXPIRED
            req.resolved_at = datetime.now(timezone.utc).isoformat()
            req.resolved_by = "timeout"
            return False
        finally:
            self._approval_futures.pop(request_id, None)

    def resolve_request(self, request_id: str, approved: bool, resolved_by: str = "user") -> bool:
        req = self._pending_requests.get(request_id)
        if not req or req.status != ApprovalStatus.PENDING:
            return False

        req.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        req.resolved_at = datetime.now(timezone.utc).isoformat()
        req.resolved_by = resolved_by

        fut = self._approval_futures.get(request_id)
        if fut and not fut.done():
            fut.set_result(approved)

        return True

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._pending_requests.get(request_id)

    def list_pending_requests(self) -> List[ApprovalRequest]:
        return [r for r in self._pending_requests.values() if r.status == ApprovalStatus.PENDING]
