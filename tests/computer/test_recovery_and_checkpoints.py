"""
Unit tests for Phase 17 Recovery Engine, Loop Detection, Checkpoints, and Rollback.
"""

from pathlib import Path
import pytest
from core.computer.checkpoint_engine import CheckpointEngine
from core.computer.models import (
    ActionType,
    ApplicationContext,
    ComputerAction,
    DesktopObservation,
    ErrorType,
)
from core.computer.recovery_engine import ComputerRecoveryEngine, LoopDetector


def test_loop_detection_repeated_actions():
    detector = LoopDetector(max_repeats=3)
    action = ComputerAction(action_type=ActionType.CLICK, target="Next")
    obs = DesktopObservation(active_window="Wizard Step 1")

    # Repeat action 3 times
    detector.record_step(action, obs)
    assert detector.is_loop_detected() is False
    detector.record_step(action, obs)
    assert detector.is_loop_detected() is False
    detector.record_step(action, obs)
    assert detector.is_loop_detected() is True


def test_loop_detection_oscillating_states():
    detector = LoopDetector(max_repeats=3)
    action_a = ComputerAction(action_type=ActionType.CLICK, target="Tab A")
    action_b = ComputerAction(action_type=ActionType.CLICK, target="Tab B")

    obs_a = DesktopObservation(active_window="Window A")
    obs_b = DesktopObservation(active_window="Window B")

    # A -> B -> A -> B
    detector.record_step(action_a, obs_a)
    detector.record_step(action_b, obs_b)
    detector.record_step(action_a, obs_a)
    detector.record_step(action_b, obs_b)

    assert detector.is_loop_detected() is True


def test_error_classification_and_strategy():
    recovery = ComputerRecoveryEngine()

    err_auth = recovery.classify_error("Login authentication required to proceed.")
    assert err_auth == ErrorType.AUTH_REQUIRED
    strat_auth = recovery.select_recovery_strategy(
        err_auth, ComputerAction(action_type=ActionType.CLICK), retry_count=1
    )
    assert strat_auth["strategy"] == "PAUSE_FOR_HUMAN"

    err_not_found = recovery.classify_error("Element 'Submit' not found on screen.")
    assert err_not_found == ErrorType.ELEMENT_NOT_FOUND
    strat_nf = recovery.select_recovery_strategy(
        err_not_found, ComputerAction(action_type=ActionType.CLICK), retry_count=1
    )
    assert strat_nf["strategy"] == "REOBSERVE_AND_SEARCH_OCR"


def test_checkpointing_and_rollback(tmp_path: Path):
    ckpt_engine = CheckpointEngine(checkpoints_dir=str(tmp_path / "checkpoints"))

    # 1. Create checkpoint
    ctx = ApplicationContext(app_name="TestApp", window_title="Test App")
    ckpt = ckpt_engine.create_checkpoint(
        task_id="task_123",
        step_index=2,
        app_context=ctx,
        completed_actions=[{"type": "open", "app": "TestApp"}],
        pending_steps=["Install dependencies", "Run tests", "Export report"],
    )

    loaded = ckpt_engine.get_latest_checkpoint("task_123")
    assert loaded is not None
    assert loaded.task_id == "task_123"
    assert loaded.step_index == 2

    # 2. Test safe resume (if report already exists, skips export)
    remaining = ckpt_engine.plan_safe_resume(
        checkpoint=loaded,
        current_app_context=ctx,
        existing_artifacts=["report"],
    )
    assert len(remaining) == 2
    assert "Export report" not in remaining

    # 3. Test rollback file creation
    test_file = tmp_path / "temp_artifact.txt"
    test_file.write_text("temporary data")
    ckpt_engine.record_rollback_action("file_create", {"path": str(test_file)})

    assert test_file.exists()
    rollback_res = ckpt_engine.execute_rollback()
    assert len(rollback_res) == 1
    assert rollback_res[0]["success"] is True
    assert not test_file.exists()
