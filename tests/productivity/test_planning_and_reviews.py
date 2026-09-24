"""
Unit tests for Phase 16 Daily Planning, Focus Mode, and Reviews.
"""

from pathlib import Path
import pytest
from core.productivity.models import PlanStatus, TaskPriority
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_daily_plan_generation_and_capacity_warning(temp_prod: ProductivityOrchestrator):
    # Create several heavy tasks (e.g. 5 tasks * 120 min = 600 min > 300 min available)
    for i in range(5):
        temp_prod.tasks.create_task(
            title=f"Heavy Task {i+1}",
            estimated_duration_minutes=120,
            priority=TaskPriority.HIGH,
        )

    # Ask to plan day with only 4 hours (240 min)
    plan, warning = temp_prod.planning.generate_daily_plan(available_minutes=240)
    assert plan.status == PlanStatus.PROPOSED
    assert warning is not None
    assert "Schedule Overload" in warning
    assert plan.total_planned_minutes <= 240

    # User accepts plan
    accepted = temp_prod.planning.accept_plan(plan.id)
    assert accepted is True
    saved_plan = temp_prod.store.get_daily_plan(plan.date)
    assert saved_plan.status == PlanStatus.ACCEPTED


def test_focus_mode_lifecycle(temp_prod: ProductivityOrchestrator):
    task = temp_prod.tasks.create_task(title="Deep Implementation")

    # Start session
    session = temp_prod.focus.start_focus_session(task_id=task.id, duration_minutes=45)
    assert temp_prod.focus.is_focusing is True
    assert session.task_id == task.id

    # Record interruption
    temp_prod.focus.record_interruption()
    assert session.interruptions == 1

    # End session
    ended = temp_prod.focus.end_focus_session(completed=True, notes="Great focus block")
    assert temp_prod.focus.is_focusing is False
    assert ended.completed is True


def test_weekly_review_generation(temp_prod: ProductivityOrchestrator):
    project = temp_prod.projects.create_project(name="Project X")
    t1 = temp_prod.tasks.create_task(title="Task 1", project_id=project.id)
    temp_prod.tasks.complete_task(t1.id, execution_output={"manually_confirmed": True})

    review = temp_prod.reviews.generate_weekly_review()
    assert review["completed_tasks_count"] == 1
    assert "Project X" in review["projects_advanced"]
