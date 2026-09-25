"""
Red-Team Adversarial Matrix: Stuck Task Detection & Emergency Kill-Switch (Phase 20)
Verifies TaskWatchdog detection of infinite loops, step limits, timeout halts,
and EmergencyController immediate global kill-switch abortion.
"""

import asyncio
import pytest

from core.orchestrator.watchdog import TaskWatchdog
from core.orchestrator.emergency import EmergencyController, EmergencyState
from core.orchestrator.state_machine import TaskState
from core.tasks.task import Task, TaskStatus


def test_watchdog_detects_repeated_action_loops():
    """Verifies that an agent repeatedly calling the exact same tool and arguments is flagged as stuck."""
    task = Task(user_request="Looping agent task")
    watchdog = TaskWatchdog(task=task, max_repeated_actions=3)

    # 1st and 2nd repeated action are allowed
    assert watchdog.record_action("browser_click", {"x": 100, "y": 200}) is True
    assert watchdog.record_action("browser_click", {"x": 100, "y": 200}) is True

    # 3rd repeated action triggers loop detection
    is_allowed = watchdog.record_action("browser_click", {"x": 100, "y": 200})
    assert is_allowed is False
    assert task.status == TaskStatus.BLOCKED
    assert "Repeated action loop" in task.error


def test_watchdog_detects_repeated_error_threshold():
    """Verifies that 3 consecutive identical tool execution errors halt the task into BLOCKED."""
    task = Task(user_request="Erroring task")
    watchdog = TaskWatchdog(task=task, max_repeated_errors=3)

    watchdog.record_error("Connection refused to target port 8080")
    watchdog.record_error("Connection refused to target port 8080")
    watchdog.record_error("Connection refused to target port 8080")

    is_stuck, reason = watchdog.check_health()
    assert is_stuck is True
    assert "Repeated error threshold" in reason
    assert task.status == TaskStatus.BLOCKED


def test_watchdog_enforces_step_limit():
    """Verifies that exceeding the maximum step limit transitions task to BLOCKED."""
    task = Task(user_request="Runaway task")
    watchdog = TaskWatchdog(task=task, max_steps=5)

    for i in range(5):
        watchdog.record_action(f"tool_{i}", {"step": i})

    is_stuck, reason = watchdog.check_health()
    assert is_stuck is True
    assert "Step limit exceeded" in reason
    assert task.status == TaskStatus.BLOCKED


def test_emergency_controller_kill_switch_lifecycle():
    """Verifies global emergency stop kill-switch, blocking action execution, and resumption."""
    controller = EmergencyController()

    # Normal state allows execution
    assert controller.state == EmergencyState.NORMAL
    assert controller.can_execute_action() is True

    # Trigger global kill-switch
    aborted_tasks = controller.abort_all(reason="Adversarial anomaly detected")
    assert controller.state == EmergencyState.STOPPED
    assert controller.can_execute_action() is False

    # In STOPPED state, any action attempt is strictly rejected
    with pytest.raises(RuntimeError) as exc_info:
        controller.assert_can_execute()
    assert "Emergency stop is ACTIVE" in str(exc_info.value)

    # Resume normal operation
    controller.resume()
    assert controller.state == EmergencyState.NORMAL
    assert controller.can_execute_action() is True
