"""
Unit tests for Phase 16 Task Completion Gate, Artifact Verification, and Cross-Project Isolation.
"""

from pathlib import Path
import pytest
from core.productivity.models import TaskStatus
from core.productivity.orchestrator import ProductivityOrchestrator
from core.productivity.verification_gate import TaskCompletionGate


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_completion_gate_requires_evidence_or_manual_confirmation(temp_prod: ProductivityOrchestrator):
    task = temp_prod.tasks.create_task(title="Deploy Release")

    # Empty execution output without manual confirmation fails
    verified, failures = temp_prod.tasks.complete_task(task.id, execution_output={})
    assert verified is False
    assert any("No execution output" in f for f in failures)
    # Task remains TODO
    reloaded = temp_prod.store.get_task(task.id)
    assert reloaded.status == TaskStatus.TODO


def test_completion_gate_artifact_verification(temp_prod: ProductivityOrchestrator, tmp_path: Path):
    real_artifact = tmp_path / "report.pdf"
    real_artifact.write_text("dummy report content")

    fake_artifact = tmp_path / "nonexistent.pdf"

    task = temp_prod.tasks.create_task(title="Generate Report")

    # Trying to complete with missing artifact fails
    verified, failures = temp_prod.tasks.complete_task(
        task.id, execution_output={"artifact_path": str(fake_artifact)}
    )
    assert verified is False
    assert any("do not exist on disk" in f for f in failures)

    # Completing with existing artifact succeeds
    verified_ok, failures_ok = temp_prod.tasks.complete_task(
        task.id, execution_output={"artifact_path": str(real_artifact)}
    )
    assert verified_ok is True
    reloaded = temp_prod.store.get_task(task.id)
    assert reloaded.status == TaskStatus.COMPLETED


def test_cross_project_file_boundary_safety(temp_prod: ProductivityOrchestrator, tmp_path: Path):
    proj_a_dir = tmp_path / "project_a"
    proj_b_dir = tmp_path / "project_b"
    proj_a_dir.mkdir(parents=True, exist_ok=True)
    proj_b_dir.mkdir(parents=True, exist_ok=True)

    project_a = temp_prod.projects.create_project(name="Project A", codebase_path=str(proj_a_dir))
    temp_prod.context.set_active_project(project_a.id)

    # File inside project_a is allowed
    allowed_file = proj_a_dir / "src" / "main.py"
    ok, msg = temp_prod.context.verify_project_file_boundary(str(allowed_file))
    assert ok is True

    # File in project_b is blocked under project_a context
    foreign_file = proj_b_dir / "src" / "other.py"
    blocked, reason = temp_prod.context.verify_project_file_boundary(str(foreign_file))
    assert blocked is False
    assert "Cross-project safety violation" in reason
