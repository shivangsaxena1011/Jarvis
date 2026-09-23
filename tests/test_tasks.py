"""
Unit tests for SHIVANI Task Model & Lifecycle.
"""

from core.tasks.task import Task, TaskStatus, TaskPriority, TaskPlan, PlanStep


def test_task_creation_and_defaults():
    task = Task(user_request="Open Chrome")
    assert task.user_request == "Open Chrome"
    assert task.user_query == "Open Chrome"
    assert task.status == TaskStatus.PENDING
    assert task.state == TaskStatus.PENDING
    assert task.priority == TaskPriority.MEDIUM
    assert task.plan is None
    assert task.current_step == 0


def test_task_state_transition():
    task = Task(user_request="Inspect workspace")
    task.transition_to(TaskStatus.PLANNING, "Formulating plan", details={"tools": 5})
    assert task.status == TaskStatus.PLANNING
    assert task.metadata["tools"] == 5
    assert task.metadata["last_message"] == "Formulating plan"

    task.transition_to(TaskStatus.COMPLETED, "Done")
    assert task.status == TaskStatus.COMPLETED


def test_task_plan_structure():
    plan = TaskPlan(
        goal="Open and verify Chrome",
        rationale="Step-by-step launch and window check",
        steps=[
            PlanStep(
                id="1",
                tool="computer.open_app",
                action="Launch chrome.exe",
                arguments={"app_name": "chrome.exe"},
                expected_outcome="Process detected"
            )
        ]
    )
    assert len(plan.steps) == 1
    assert plan.steps[0].tool == "computer.open_app"
