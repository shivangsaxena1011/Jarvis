"""
Unit tests for Phase 15 Idempotency Guards, Retries with Exponential Backoff, and Failure Policies.
"""

from pathlib import Path
import pytest

from core.automation.models import (
    Automation,
    AutomationPermissions,
    AutomationStep,
    FailurePolicy,
    RunStatus,
    TriggerConfig,
    TriggerType,
)
from core.automation.runner import AutomationRunner
from core.automation.store import AutomationStore
from security.permissions.engine import PermissionEngine
from security.permissions.models import RiskLevel


@pytest.fixture
def temp_store(tmp_path: Path):
    return AutomationStore(db_path=tmp_path / "test_automations.db")


@pytest.mark.asyncio
async def test_idempotency_prevents_duplicate_execution(temp_store: AutomationStore):
    pe = PermissionEngine()
    execution_counter = 0

    def mock_dispatcher(tool: str, args: dict):
        nonlocal execution_counter
        execution_counter += 1
        return {"result": "success", "count": execution_counter}

    runner = AutomationRunner(
        store=temp_store,
        permission_engine=pe,
        tool_dispatcher=mock_dispatcher,
    )

    auto = Automation(
        name="Idempotent Task",
        trigger=TriggerConfig(type=TriggerType.INTERVAL),
        steps=[
            AutomationStep(
                step_id="step1",
                name="Send Message Once",
                action="email.send",
                input_template={"to": "user@example.com", "body": "Weekly Report"},
                idempotency_key="static_key_12345",
                risk_level=RiskLevel.SAFE,
            )
        ],
        permissions=AutomationPermissions(
            allowed_capabilities=["email"],
            max_risk_level=RiskLevel.SAFE,
        ),
    )
    temp_store.save_automation(auto)

    # First run: should execute
    run1 = await runner.run_automation(auto)
    assert run1.status == RunStatus.COMPLETED
    assert execution_counter == 1
    assert run1.steps[0].status == "COMPLETED"

    # Second run: should be skipped due to duplicate idempotency key
    run2 = await runner.run_automation(auto)
    assert run2.status == RunStatus.COMPLETED
    assert execution_counter == 1  # Dispatcher NOT called second time!
    assert run2.steps[0].status == "SKIPPED_DUPLICATE"


@pytest.mark.asyncio
async def test_retry_policy_with_exponential_backoff(temp_store: AutomationStore):
    pe = PermissionEngine()
    attempts = 0

    def failing_dispatcher(tool: str, args: dict):
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Temporary network drop")
        return {"status": "recovered"}

    runner = AutomationRunner(
        store=temp_store,
        permission_engine=pe,
        tool_dispatcher=failing_dispatcher,
    )

    auto = Automation(
        name="Retryable Workflow",
        trigger=TriggerConfig(type=TriggerType.INTERVAL),
        steps=[
            AutomationStep(
                step_id="s1",
                action="research.search",
                tool="research.search",
                input_template={"query": "AI"},
                retry_count=3,
                failure_policy=FailurePolicy.RETRY,
                risk_level=RiskLevel.SAFE,
            )
        ],
        permissions=AutomationPermissions(
            allowed_capabilities=["research"],
            max_risk_level=RiskLevel.SAFE,
        ),
    )
    temp_store.save_automation(auto)

    run = await runner.run_automation(auto)
    assert run.status == RunStatus.COMPLETED
    assert attempts == 3  # Tried 3 times and recovered!
    assert run.steps[0].status == "COMPLETED"
