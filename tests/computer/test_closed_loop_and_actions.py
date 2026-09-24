"""
Unit tests for Phase 17 Closed-Loop Execution, Expectation Engine, and Action Verification.
"""

import pytest
from core.computer.execution_engine import ExecutionEngine
from core.computer.expectation_engine import ExpectationEngine
from core.computer.models import (
    ActionType,
    ComputerAction,
    DesktopObservation,
    ElementType,
    RectBounds,
    UIElement,
)
from core.computer.resource_lock import ActionPriority, ResourceLockManager
from core.computer.synthetic import SyntheticGUIEnvironment
from tools.desktop.os.mock import MockOperatingSystemAdapter


@pytest.mark.asyncio
async def test_closed_loop_action_verified():
    env = SyntheticGUIEnvironment()
    pre_obs = env.generate_form_screen("Unsaved Document")
    post_obs = env.generate_form_screen("Document (Saved)")

    mock_os = MockOperatingSystemAdapter()
    engine = ExecutionEngine(os_adapter=mock_os)

    action = ComputerAction(
        action_type=ActionType.CLICK,
        target="Save",
        expected_state={"state_should_change": True, "window_title": "Saved"},
    )

    res = await engine.execute_closed_loop(
        action=action, pre_observation=pre_obs, synthetic_post_obs=post_obs
    )

    assert res.verified is True
    assert res.success is True
    assert res.state_diff.active_window_changed is True
    assert res.state_diff.new_window_title == "Document (Saved)"


@pytest.mark.asyncio
async def test_closed_loop_action_expectation_failure():
    env = SyntheticGUIEnvironment()
    pre_obs = env.generate_form_screen("Unsaved Document")
    # Same screen returned post-action (nothing changed)
    post_obs = env.generate_form_screen("Unsaved Document")

    mock_os = MockOperatingSystemAdapter()
    engine = ExecutionEngine(os_adapter=mock_os)

    # Action expected a window title change
    action = ComputerAction(
        action_type=ActionType.CLICK,
        target="Save",
        expected_state={"window_title": "Saved Successfully"},
    )

    res = await engine.execute_closed_loop(
        action=action, pre_observation=pre_obs, synthetic_post_obs=post_obs
    )

    assert res.verified is False
    assert res.failure_reason is not None
    assert "Expected active window containing 'Saved Successfully'" in res.failure_reason


@pytest.mark.asyncio
async def test_emergency_stop_halts_execution():
    mock_os = MockOperatingSystemAdapter()
    lock_mgr = ResourceLockManager()
    engine = ExecutionEngine(os_adapter=mock_os, lock_manager=lock_mgr)

    # Activate emergency stop
    lock_mgr.emergency_stop()

    action = ComputerAction(action_type=ActionType.CLICK, target="Button")
    res = await engine.execute_closed_loop(action=action)

    assert res.success is False
    assert "Emergency stop is active" in res.failure_reason
