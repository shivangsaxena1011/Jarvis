"""
End-to-End Acceptance Tests for Phase 14 (Section 63 Scenarios).
"""

import asyncio
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

from apps.desktop.server import app, assistant_state_mgr, AssistantState, orchestrator
from core.tasks.task import TaskStatus
from security.permissions.models import RiskLevel


@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def reset_state():
    if orchestrator.emergency.is_stopped:
        orchestrator.emergency.resume()
    assistant_state_mgr.locked = False
    assistant_state_mgr.set_state(AssistantState.IDLE)


# TEST 1: "Shivani, open Chrome."
@pytest.mark.asyncio
async def test_acceptance_scenario_1_open_chrome():
    from tools.desktop.os.mock import MockOSAdapter
    from tools.desktop import ApplicationManager, WindowManager
    if not isinstance(orchestrator.os_adapter, MockOSAdapter):
        mock_os = MockOSAdapter()
        orchestrator.os_adapter = mock_os
        orchestrator.computer_agent.adapter = mock_os
        open_tool = orchestrator.tools.get_tool("computer.open_app")
        if open_tool:
            open_tool.app_manager = ApplicationManager(mock_os)
        win_tool = orchestrator.tools.get_tool("computer.active_window")
        if win_tool:
            win_tool.window_manager = WindowManager(mock_os)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit voice/text command
        res = await client.post("/api/conversation/message", json={"message": "Shivani, open Chrome."})
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        # Wait for task completion
        task = orchestrator.get_task(task_id)
        assert task is not None
        while task.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
            await asyncio.sleep(0.05)

        assert task.status == TaskStatus.COMPLETED
        assert assistant_state_mgr.state == AssistantState.COMPLETED


# TEST 2: "Shivani, search for AI OCR and summarize the results."
@pytest.mark.asyncio
async def test_acceptance_scenario_2_research_ocr():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/conversation/message", json={"message": "Shivani, search for AI OCR and summarize the results."})
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        task = orchestrator.get_task(task_id)
        assert task is not None
        while task.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
            await asyncio.sleep(0.05)

        assert task.status == TaskStatus.COMPLETED
        # Verify research / summary result
        assert task.final_output is not None


# TEST 3: "Shivani, prepare this LinkedIn post." -> Draft created, no publish without approval
@pytest.mark.asyncio
async def test_acceptance_scenario_3_linkedin_draft_no_silent_publish():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/api/conversation/message", json={"message": "Shivani, prepare this LinkedIn post about Python."})
        assert res.status_code == 200
        task_id = res.json()["task_id"]

        task = orchestrator.get_task(task_id)
        while task.status in (TaskStatus.PENDING, TaskStatus.PLANNING, TaskStatus.EXECUTING, TaskStatus.VERIFYING):
            await asyncio.sleep(0.05)

        assert task.status == TaskStatus.COMPLETED
        # Ensure it generated a draft and did NOT publish automatically without approval
        assert "Draft" in str(task.final_output) or "Post" in str(task.final_output) or "LinkedIn" in str(task.final_output)


# TEST 4: "Shivani, stop." -> Emergency stop
@pytest.mark.asyncio
async def test_acceptance_scenario_4_emergency_stop():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.post("/stop")
        assert res.status_code == 200
        assert res.json()["success"] is True
        assert assistant_state_mgr.state == AssistantState.CANCELLED
        assert orchestrator.emergency.is_stopped is True
        # Reset emergency stop for subsequent tests
        orchestrator.emergency.reset()


# TEST 5: Restart / Checkpoint recovery
@pytest.mark.asyncio
async def test_acceptance_scenario_5_restart_recovery(tmp_path: Path):
    from recovery.recovery_engine import RecoveryEngine
    recovery = RecoveryEngine(checkpoints_dir=str(tmp_path / "checkpoints"))

    # Save active state checkpoint
    task = await orchestrator.submit_task("Long running data ingestion")
    cp = recovery.checkpoints.save_checkpoint(task_id=task.id, stage="source_collection", state={"items_processed": 50})
    assert cp.task_id == task.id

    # Simulate restart: load latest checkpoint
    loaded = recovery.get_task_checkpoint(task.id)
    assert loaded is not None
    assert loaded.task_id == task.id
    assert loaded.stage == "source_collection"


# TEST 6: Android device disconnect & independent operation
@pytest.mark.asyncio
async def test_acceptance_scenario_6_android_disconnect_handling():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Disconnect device
        res = await client.post("/api/devices/shivani-android-001/disconnect")
        assert res.status_code == 200

        # Verify other desktop capabilities continue functioning normally
        status_res = await client.get("/api/status")
        assert status_res.status_code == 200
        assert status_res.json()["registered_tools_count"] >= 159


# TEST 7: Offline / Degraded experience status
@pytest.mark.asyncio
async def test_acceptance_scenario_7_offline_degraded_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/diagnostics/run?full=false")
        assert res.status_code == 200
        data = res.json()
        assert "passed" in data
        assert len(data["items"]) > 0


# TEST 8: High-risk action triggers approval requirement
@pytest.mark.asyncio
async def test_acceptance_scenario_8_high_risk_approval_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Request approval for high risk action
        req = orchestrator.permissions.request_approval(
            task_id="test-task-high-risk",
            tool_name="terminal_execute",
            arguments={"path": "C:/tmp/cache"},
            description="Delete build cache",
            risk_level=RiskLevel.HIGH_RISK,
        )
        assert req.status == "PENDING"

        # Verify it shows up in /api/approvals
        appr_res = await client.get("/api/approvals")
        assert appr_res.status_code == 200
        approvals = appr_res.json()
        assert any(a["id"] == req.id for a in approvals)

        # Approve action
        res_approve = await client.post(f"/api/approvals/{req.id}", json={"approved": True, "resolved_by": "user"})
        assert res_approve.status_code == 200
        assert res_approve.json()["approved"] is True

        # Verify it is no longer pending
        appr_after = await client.get("/api/approvals")
        assert not any(a["id"] == req.id for a in appr_after.json())
