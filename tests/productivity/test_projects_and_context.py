"""
Unit tests for Phase 16 Projects, Context Engine, Decisions, and Blockers.
"""

from pathlib import Path
import pytest
from core.productivity.models import TaskPriority, TaskStatus
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_project_creation_and_context(temp_prod: ProductivityOrchestrator, tmp_path: Path):
    code_dir = tmp_path / "ocr_codebase"
    code_dir.mkdir(parents=True, exist_ok=True)

    project = temp_prod.projects.create_project(
        name="Shivani OCR",
        description="Visual document scanner",
        priority=TaskPriority.HIGH,
        codebase_path=str(code_dir),
    )

    assert project.id.startswith("proj_")
    assert project.name == "Shivani OCR"

    # Context Engine
    ctx = temp_prod.context.get_project_context(project.id)
    assert ctx["project_name"] == "Shivani OCR"
    assert ctx["open_tasks_count"] == 0
    assert ctx["blocked_tasks_count"] == 0


def test_project_continuity_summary(temp_prod: ProductivityOrchestrator):
    project = temp_prod.projects.create_project(name="OCR Engine")
    temp_prod.tasks.create_task(title="Build Pipeline", project_id=project.id)
    temp_prod.tasks.create_task(title="Implement Tesseract Adapter", project_id=project.id)

    summary = temp_prod.context.get_continuity_summary("OCR Engine")
    assert summary["found"] is True
    assert summary["project_name"] == "OCR Engine"
    assert "2 unfinished task(s)" in summary["summary_message"]
    assert len(summary["unfinished_tasks"]) == 2


def test_decisions_and_blockers(temp_prod: ProductivityOrchestrator):
    project = temp_prod.projects.create_project(name="Core Runtime")

    # Record decision
    dec = temp_prod.projects.record_decision(
        project_id=project.id,
        topic="Browser Automation",
        decision="Use Playwright",
        reason="Stable accessibility and DOM inspection",
    )
    assert dec.topic == "Browser Automation"

    decisions = temp_prod.store.list_decisions(project_id=project.id)
    assert len(decisions) == 1

    # Record blocker and verify affected tasks transition to BLOCKED
    task = temp_prod.tasks.create_task(title="Deploy to Cloud", project_id=project.id)
    assert task.status == TaskStatus.TODO

    blocker = temp_prod.projects.record_blocker(
        project_id=project.id,
        title="Firewall Config Missing",
        description="Port 443 closed by network admin",
        affected_tasks=[task.id],
    )
    task_reloaded = temp_prod.store.get_task(task.id)
    assert task_reloaded.status == TaskStatus.BLOCKED

    # Resolve blocker
    temp_prod.projects.resolve_blocker(blocker.id, resolution="Firewall rule created")
    task_unblocked = temp_prod.store.get_task(task.id)
    assert task_unblocked.status == TaskStatus.TODO
