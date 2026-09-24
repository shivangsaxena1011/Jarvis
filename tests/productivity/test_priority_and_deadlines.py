"""
Unit tests for Phase 16 Multi-Factor Priority Engine and Deadline Engine.
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from core.productivity.models import PersonalTask, TaskPriority
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_multi_factor_priority_scoring(temp_prod: ProductivityOrchestrator):
    tomorrow = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")

    # Low priority task without deadline
    t_low = temp_prod.tasks.create_task(title="Organize bookmarks", priority=TaskPriority.LOW)

    # Critical task due tomorrow that unblocks other tasks
    t_crit = temp_prod.tasks.create_task(
        title="Fix production security flaw",
        priority=TaskPriority.CRITICAL,
        due_date=tomorrow,
    )
    t_dep = temp_prod.tasks.create_task(title="Deploy to users", dependencies=[t_crit.id])

    all_tasks = [t_low, t_crit, t_dep]
    score_low = temp_prod.priority.evaluate_task(t_low, all_tasks)
    score_crit = temp_prod.priority.evaluate_task(t_crit, all_tasks)

    assert score_crit.total_score > score_low.total_score
    # Verify transparent reasons
    assert any("CRITICAL" in r for r in score_crit.reasons)
    assert any("Blocks" in r for r in score_crit.reasons)
    assert any("approaching" in r or "24 hours" in r for r in score_crit.reasons)


def test_deadline_categorization_and_conflicts(temp_prod: ProductivityOrchestrator):
    now = datetime.now(timezone.utc)
    yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")
    today = now.strftime("%Y-%m-%d")
    next_week = (now + timedelta(days=5)).strftime("%Y-%m-%d")

    t_overdue = temp_prod.tasks.create_task(title="Submit taxes", due_date=yesterday)
    t_today = temp_prod.tasks.create_task(title="Team sync", due_date=today)
    t_week = temp_prod.tasks.create_task(title="Review PR", due_date=next_week)

    buckets = temp_prod.deadlines.categorize_deadlines([t_overdue, t_today, t_week])
    assert len(buckets["overdue"]) == 1
    assert buckets["overdue"][0].id == t_overdue.id
    assert len(buckets["today"]) == 1
    assert len(buckets["this_week"]) == 1

    # Conflict detection: Dependency Due Date Inversion
    t_dep = temp_prod.tasks.create_task(title="Architecture Spec", due_date=next_week)
    t_impl = temp_prod.tasks.create_task(
        title="Implementation",
        due_date=today,
        dependencies=[t_dep.id],
    )
    conflicts = temp_prod.deadlines.detect_conflicts([t_dep, t_impl])
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "DEPENDENCY_DEADLINE_INVERSION"
