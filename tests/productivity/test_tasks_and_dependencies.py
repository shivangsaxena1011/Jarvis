"""
Unit tests for Phase 16 Tasks, Dependency DAGs, Cycle Detection, and NL Parsing.
"""

from pathlib import Path
import pytest
from core.productivity.models import PersonalTask, TaskPriority, TaskStatus
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_natural_language_task_parsing(temp_prod: ProductivityOrchestrator):
    project = temp_prod.projects.create_project(name="OCR")

    # Prompt with relative due date
    t1 = temp_prod.tasks.parse_natural_language_task(
        "Remind me to finish the README tomorrow",
        active_project_id=project.id,
    )
    assert "README" in t1.title or "Finish" in t1.title
    assert t1.due_date is not None
    assert t1.project_id == project.id

    # Prompt with project in name and urgency
    t2 = temp_prod.tasks.parse_natural_language_task("Urgent testing for OCR project")
    assert t2.priority == TaskPriority.CRITICAL
    assert t2.project_id == project.id


def test_dependency_dag_and_cycle_detection(temp_prod: ProductivityOrchestrator):
    t_a = temp_prod.tasks.create_task(title="Task A")
    t_b = temp_prod.tasks.create_task(title="Task B", dependencies=[t_a.id])
    t_c = temp_prod.tasks.create_task(title="Task C", dependencies=[t_b.id])

    all_tasks = [t_a, t_b, t_c]

    # No cycles
    cycles = temp_prod.dependencies.detect_cycles(all_tasks)
    assert len(cycles) == 0

    # Introduce cycle: Task A depends on Task C
    t_a.dependencies.append(t_c.id)
    cycles = temp_prod.dependencies.detect_cycles(all_tasks)
    assert len(cycles) > 0


def test_blocker_propagation(temp_prod: ProductivityOrchestrator):
    t_arch = temp_prod.tasks.create_task(title="Architecture")
    t_impl = temp_prod.tasks.create_task(title="Implementation", dependencies=[t_arch.id])

    all_map = {t_arch.id: t_arch, t_impl.id: t_impl}

    # t_impl should be blocked while t_arch is TODO
    is_blocked, reasons = temp_prod.dependencies.get_blocked_status(t_impl, all_map)
    assert is_blocked is True
    assert any("Architecture" in r for r in reasons)

    # Mark t_arch complete
    temp_prod.tasks.complete_task(t_arch.id, execution_output={"manually_confirmed": True})
    t_arch_done = temp_prod.store.get_task(t_arch.id)
    all_map[t_arch.id] = t_arch_done

    is_blocked_now, _ = temp_prod.dependencies.get_blocked_status(t_impl, all_map)
    assert is_blocked_now is False
