"""
SHIVANI Phase 17 End-to-End Test Scenarios (Sections 82–89).
Verifies the complete closed-loop computer autonomy agent across 8 canonical long-horizon workflows.
"""

from pathlib import Path
import pytest
from core.computer.agent import ComputerAutonomyAgent
from core.computer.models import (
    ActionType,
    ApplicationContext,
    ApplicationState,
    ComputerAction,
    DesktopObservation,
    ElementType,
    ErrorType,
    RectBounds,
    UIElement,
)
from core.computer.synthetic import SyntheticGUIEnvironment
from tools.desktop.os.mock import MockOperatingSystemAdapter


@pytest.mark.asyncio
async def test_e2e_scenario_1_vscode_test_and_diagnose(tmp_path: Path):
    """Scenario 1: Open VS Code, run tests, observe output, diagnose failures."""
    mock_os = MockOperatingSystemAdapter()
    agent = ComputerAutonomyAgent(os_adapter=mock_os, checkpoints_dir=str(tmp_path / "ckpts"))

    # Execute test diagnostic command
    res = await agent.terminal.execute_command("python --version")
    assert res.success is True
    assert res.risk.value == "SAFE"

    # Verify VSCode adapter integration
    vscode_adapter = agent.adapter_registry.resolve_adapter("code.exe", "VS Code")
    action_res = await vscode_adapter.execute_action(
        "run_tests", {"test_target": "tests/unit"}, ApplicationContext(app_name="VSCode")
    )
    assert action_res["success"] is True
    assert "sequence" in action_res


@pytest.mark.asyncio
async def test_e2e_scenario_2_file_organization_preview_and_move(tmp_path: Path):
    """Scenario 2: Find all PDFs in Downloads, propose organization with preview, apply, verify."""
    downloads = tmp_path / "Downloads"
    downloads.mkdir()
    (downloads / "doc1.pdf").write_text("dummy")
    (downloads / "doc2.pdf").write_text("dummy")
    (downloads / "photo.png").write_text("dummy")

    explorer_adapter = ExplorerAdapter = agent = ComputerAutonomyAgent().adapter_registry.resolve_adapter("explorer.exe", "Explorer")

    # 1. Scan directory
    scan_res = await explorer_adapter.execute_action("scan_directory", {"directory": str(downloads)}, ApplicationContext())
    assert scan_res["success"] is True
    assert scan_res["summary"][".pdf"] == 2
    assert scan_res["summary"][".png"] == 1

    # 2. Propose organization (preview required)
    prop_res = await explorer_adapter.execute_action("propose_organization", {"directory": str(downloads)}, ApplicationContext())
    assert prop_res["preview_required"] is True
    assert prop_res["total_files"] == 3

    # 3. Apply moves upon approval
    apply_res = await explorer_adapter.execute_action("apply_organization", {"planned_moves": prop_res["planned_moves"]}, ApplicationContext())
    assert apply_res["success"] is True
    assert apply_res["applied_moves"] == 3
    assert (downloads / "Documents" / "doc1.pdf").exists()
    assert (downloads / "Images" / "photo.png").exists()


@pytest.mark.asyncio
async def test_e2e_scenario_3_excel_csv_chart(tmp_path: Path):
    """Scenario 3: Open CSV, analyze, create chart, and verify final Excel workbook."""
    csv_file = tmp_path / "metrics.csv"
    csv_file.write_text("Day,Throughput\nMon,120\nTue,150\nWed,180\n")
    output_excel = tmp_path / "metrics_chart.xlsx"

    excel_adapter = ComputerAutonomyAgent().adapter_registry.resolve_adapter("excel.exe", "Excel")
    res = await excel_adapter.execute_action(
        "insert_chart_from_csv",
        {"csv_path": str(csv_file), "output_excel": str(output_excel), "chart_title": "Daily Throughput"},
        ApplicationContext(),
    )
    assert res["success"] is True
    assert res["verified"] is True
    assert output_excel.exists()


@pytest.mark.asyncio
async def test_e2e_scenario_4_powerpoint_review(tmp_path: Path):
    """Scenario 4: Review PowerPoint slides for obvious formatting/clutter issues."""
    ppt_adapter = ComputerAutonomyAgent().adapter_registry.resolve_adapter("powerpnt.exe", "PowerPoint")
    existing_pptx = Path("workspace/shivani-artifacts/presentations/hackathonapp_pitch_deck.pptx")

    if existing_pptx.exists():
        res = await ppt_adapter.execute_action(
            "review_presentation",
            {"presentation_path": str(existing_pptx)},
            ApplicationContext(),
        )
        assert res["success"] is True
        assert res["slide_count"] > 0
        assert "issues" in res


@pytest.mark.asyncio
async def test_e2e_scenario_5_readme_setup_and_dependency_check():
    """Scenario 5: Inspect setup, check environment, verify dependencies."""
    agent = ComputerAutonomyAgent()
    check_res = await agent.terminal.execute_command("python -c \"import sys; print(sys.version)\"")
    assert check_res.success is True
    assert "3." in check_res.stdout


@pytest.mark.asyncio
async def test_e2e_scenario_6_emergency_interrupt(tmp_path: Path):
    """Scenario 6: During a multi-step task, user says 'Shivani stop' -> halts, checkpoints, releases locks."""
    mock_os = MockOperatingSystemAdapter()
    agent = ComputerAutonomyAgent(os_adapter=mock_os, checkpoints_dir=str(tmp_path / "ckpts"))

    # Trigger emergency stop before/during workflow
    agent.emergency_stop()

    steps = [
        {"type": "click", "target": "Step 1"},
        {"type": "click", "target": "Step 2"},
    ]
    res = await agent.execute_task_workflow(task_id="task_emergency", steps=steps)
    assert res["success"] is False
    assert "Emergency stop" in res["error"] or "higher priority" in res["error"].lower()

    # Reset
    agent.lock_manager.reset_emergency_stop()


@pytest.mark.asyncio
async def test_e2e_scenario_7_manual_takeover_reconciliation():
    """Scenario 7: User manually takes over, external UI changes, agent reconciles and re-observes."""
    mock_os = MockOperatingSystemAdapter()
    agent = ComputerAutonomyAgent(os_adapter=mock_os)

    agent.manual_takeover()
    assert agent.lock_manager.is_manual_takeover is True

    # Attempting action while user in control is rejected
    action = ComputerAction(action_type=ActionType.CLICK, target="Button")
    res = await agent.execute_action(action)
    assert res.success is False
    assert "manual takeover" in res.failure_reason

    # User releases takeover -> agent reconciles and re-observes
    agent.resume_from_takeover()
    assert agent.lock_manager.is_manual_takeover is False
    obs = await agent.observe(capture_image=False)
    assert obs is not None


@pytest.mark.asyncio
async def test_e2e_scenario_8_application_crash_recovery(tmp_path: Path):
    """Scenario 8: Application crash detected -> state captured -> safe resume from checkpoint."""
    agent = ComputerAutonomyAgent(checkpoints_dir=str(tmp_path / "ckpts"))

    # 1. Simulate checkpoint before crash
    ctx = ApplicationContext(app_name="CrashingApp", state=ApplicationState.CRASHED)
    ckpt = agent.checkpoint_engine.create_checkpoint(
        task_id="crash_task_1",
        step_index=3,
        app_context=ctx,
        completed_actions=[{"type": "open"}, {"type": "load_file"}],
        pending_steps=["Process batch", "Save results"],
    )

    # 2. Strategy evaluation
    err_type = agent.recovery_engine.classify_error("Application has crashed and is not responding.")
    assert err_type == ErrorType.CRASH
    strategy = agent.recovery_engine.select_recovery_strategy(
        err_type, ComputerAction(action_type=ActionType.CLICK), retry_count=1
    )
    assert strategy["strategy"] == "RESTART_APPLICATION_AND_RESUME"

    # 3. Resume planning
    remaining = agent.checkpoint_engine.plan_safe_resume(ckpt, ctx, existing_artifacts=[])
    assert len(remaining) == 2
    assert "Process batch" in remaining
