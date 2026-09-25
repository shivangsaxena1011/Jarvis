"""
Real-World Acceptance Test: Automation Engine, Loop Detection & Crash Recovery.
Tests natural-language automation scheduling, loop detection logic,
and workflow state checkpoint recovery from SQLite/artifacts.
"""

from pathlib import Path
import pytest
from core.automation.engine import AutomationEngine
from core.automation.models import AutomationStatus
from core.artifacts.manager import ArtifactManager
from core.computer.recovery_engine import LoopDetector
from core.computer.models import ComputerAction, ActionType, DesktopObservation, UIElement


def test_real_automation_lifecycle(tmp_path: Path):
    """Verify natural-language automation creation, listing, preview, and toggling."""
    db_file = tmp_path / "automations.db"
    engine = AutomationEngine(db_path=db_file)
    
    # 1. Create automation from prompt
    prompt = "Every weekday at 8 AM summarize my unread emails"
    auto = engine.create_from_prompt(prompt)
    assert auto is not None
    assert auto.id is not None
    assert auto.enabled is True
    
    # 2. Preview automation
    preview = engine.preview_automation(auto)
    assert "runs" in preview or "name" in preview
    
    # 3. List automations
    all_autos = engine.list_automations()
    assert any(a.id == auto.id for a in all_autos)
    
    # 4. Disable / Enable automation
    assert engine.disable_automation(auto.id) is True
    disabled = engine.get_automation(auto.id)
    assert disabled.enabled is False
    assert disabled.status == AutomationStatus.DISABLED
    
    assert engine.enable_automation(auto.id) is True
    enabled = engine.get_automation(auto.id)
    assert enabled.enabled is True
    assert enabled.status == AutomationStatus.ACTIVE
    
    # 5. Delete automation
    assert engine.delete_automation(auto.id) is True
    remaining = [a for a in engine.list_automations() if a.id == auto.id]
    assert len(remaining) == 0


def test_loop_detector_recovery():
    """Verify loop detector catches repetitive actions and state oscillations."""
    detector = LoopDetector(history_size=10, max_repeats=3)
    
    dummy_obs = DesktopObservation(
        active_window="Notepad",
        elements=[UIElement(element_id="1", control_type="Edit", name="Text Editor", text="Hello")]
    )
    
    action = ComputerAction(
        action_type=ActionType.CLICK,
        target="button_submit",
        parameters={"text": "Submit"}
    )
    
    # Steps 1 and 2: no loop yet
    assert detector.record_step(action, dummy_obs) is False
    assert detector.record_step(action, dummy_obs) is False
    
    # Step 3: identical 3rd action -> loop detected
    assert detector.record_step(action, dummy_obs) is True
    assert detector.is_loop_detected() is True


def test_workflow_checkpoint_and_crash_recovery(tmp_path: Path):
    """Verify long-running task checkpoints can be saved and restored cleanly."""
    art_mgr = ArtifactManager(root_dir=tmp_path / "artifacts")
    
    checkpoint_data = {
        "task_id": "task_recovery_999",
        "current_step": 3,
        "completed_steps": ["init_project", "generate_scaffold", "run_linter"],
        "pending_steps": ["run_tests", "build_artifact"],
        "context_variables": {"target_dir": "src/module", "version": "1.0.0"}
    }
    
    # Save checkpoint
    cp_path = art_mgr.save_checkpoint("task_recovery_999", "step_3", checkpoint_data)
    assert cp_path.exists()
    
    # Load checkpoint
    loaded = art_mgr.load_checkpoint("task_recovery_999", "step_3")
    assert loaded is not None
    assert loaded["data"]["current_step"] == 3
    assert loaded["data"]["completed_steps"] == ["init_project", "generate_scaffold", "run_linter"]
    assert loaded["data"]["context_variables"]["version"] == "1.0.0"
