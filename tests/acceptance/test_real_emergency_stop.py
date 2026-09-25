"""
Real-world Emergency Stop & Kill-Switch Acceptance Test (Phase 20.5)
Verifies immediate task halt, blocking of new autonomous actions,
and clean resumption of normal operations.
"""

import asyncio
import pytest

from core.orchestrator.emergency import EmergencyController, EmergencyState
from core.orchestrator.state_machine import Task, TaskState


@pytest.mark.asyncio
async def test_real_emergency_kill_switch_action_halt_and_resume():
    controller = EmergencyController()
    assert controller.state == EmergencyState.NORMAL

    # Simulate active background task
    task = Task(user_query="Processing large report generation")
    task.state = TaskState.EXECUTING

    # Register task with emergency controller stop handler
    halted_event = asyncio.Event()

    def on_stop():
        task.state = TaskState.CANCELLED
        halted_event.set()

    controller.register_abort_callback("test_task_abort", on_stop)

    # Trigger emergency stop
    aborted_count = controller.abort_all(reason="User commanded 'Shivani stop'")
    assert controller.state == EmergencyState.STOPPED
    assert controller.can_execute_action() is False
    assert task.state == TaskState.CANCELLED
    assert halted_event.is_set()

    # Verify action rejection
    with pytest.raises(RuntimeError) as exc_info:
        controller.assert_can_execute()
    assert "Emergency stop is ACTIVE" in str(exc_info.value)

    # Resume system
    controller.resume()
    assert controller.state == EmergencyState.NORMAL
    assert controller.can_execute_action() is True
