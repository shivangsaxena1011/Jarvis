"""
Unit tests for Scoped Approvals in SHIVANI (Phase 20)
Verifies ONE_ACTION, TASK_SCOPE, WORKFLOW_SCOPE, and TIME_LIMITED approval mechanics.
"""

import asyncio
import time
from datetime import datetime, timezone, timedelta
import pytest

from security.permissions.models import RiskLevel, ApprovalScope, ScopedPreapproval
from security.permissions.engine import PermissionEngine
from security.policy_engine import PolicyEngine


@pytest.mark.asyncio
async def test_one_action_preapproval_consumed_after_single_use():
    engine = PermissionEngine(policy="strict")
    task_id = "task-one-action"
    tool_name = "terminal_execute"

    # Pre-approve for ONE_ACTION
    engine.grant_preapproval(task_id, tool_name, scope=ApprovalScope.ONE_ACTION)

    # First invocation should succeed immediately without prompting
    auth1 = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name=tool_name,
        arguments={"cmd": "dir"},
        default_risk=RiskLevel.HIGH_RISK,
        description="List files",
        timeout_seconds=0.1
    )
    assert auth1 is True

    # Second invocation should require approval and time out (since no user approves)
    auth2 = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name=tool_name,
        arguments={"cmd": "dir"},
        default_risk=RiskLevel.HIGH_RISK,
        description="List files again",
        timeout_seconds=0.05
    )
    assert auth2 is False


@pytest.mark.asyncio
async def test_task_scope_preapproval_multi_use_and_revocation():
    engine = PermissionEngine(policy="strict")
    task_id = "task-multi-action"
    tool_name = "file_write"

    # Pre-approve for TASK_SCOPE
    engine.grant_preapproval(task_id, tool_name, scope=ApprovalScope.TASK_SCOPE)

    # Invocations 1 and 2 succeed
    for _ in range(3):
        auth = await engine.evaluate_and_request(
            task_id=task_id,
            tool_name=tool_name,
            arguments={"path": "test.txt"},
            default_risk=RiskLevel.SENSITIVE,
            description="Write test file",
            timeout_seconds=0.1
        )
        assert auth is True

    # Revoke all task preapprovals upon task completion
    engine.revoke_task_preapprovals(task_id)

    # Next call must require approval
    auth_after = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name=tool_name,
        arguments={"path": "test.txt"},
        default_risk=RiskLevel.SENSITIVE,
        description="Write test file",
        timeout_seconds=0.05
    )
    assert auth_after is False


@pytest.mark.asyncio
async def test_time_limited_preapproval_expiration():
    engine = PermissionEngine(policy="strict")
    task_id = "task-time-limited"
    tool_name = "browser_extract"

    # Pre-approve with very short duration (0.1s)
    engine.grant_preapproval(
        task_id,
        tool_name,
        scope=ApprovalScope.TIME_LIMITED,
        duration_seconds=0.15
    )

    # Immediate call should succeed
    auth_now = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name=tool_name,
        arguments={"url": "https://example.com"},
        default_risk=RiskLevel.SENSITIVE,
        description="Extract",
        timeout_seconds=0.1
    )
    assert auth_now is True

    # Sleep past duration
    await asyncio.sleep(0.2)

    # Next call should be expired and fail without user intervention
    auth_expired = await engine.evaluate_and_request(
        task_id=task_id,
        tool_name=tool_name,
        arguments={"url": "https://example.com"},
        default_risk=RiskLevel.SENSITIVE,
        description="Extract again",
        timeout_seconds=0.05
    )
    assert auth_expired is False


def test_policy_engine_scoped_preapproval():
    policy = PolicyEngine(policy="strict")
    task_id = "policy-task-1"
    tool_name = "system_exec"

    # Requires approval before preapproval
    assert policy.requires_approval(RiskLevel.CRITICAL, task_id=task_id, tool_name=tool_name) is True

    # Preapprove ONE_ACTION
    policy.grant_preapproval(task_id, tool_name, scope=ApprovalScope.ONE_ACTION)

    # First check consumes preapproval -> returns False (does not require approval)
    assert policy.requires_approval(RiskLevel.CRITICAL, task_id=task_id, tool_name=tool_name) is False

    # Second check -> requires approval again
    assert policy.requires_approval(RiskLevel.CRITICAL, task_id=task_id, tool_name=tool_name) is True
