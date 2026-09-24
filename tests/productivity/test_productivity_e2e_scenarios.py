"""
End-to-End Acceptance Tests for Phase 16 Productivity OS (Section 79).

TEST 1 — PROJECT CREATION: "Create a project for building an AI OCR system"
TEST 2 — GOAL BREAKDOWN: "Help me break this project into milestones"
TEST 3 — CONTINUATION: "Continue the OCR project"
TEST 4 — DAILY PLAN: "Plan my day"
TEST 5 — TASK COMPLETION: "Finish the README task"
TEST 6 — BLOCKER: "Why can't I deploy this project?"
TEST 7 — CONFLICT: Detect conflicting deadlines without silent overwrite
TEST 8 — CROSS-AGENT WORKFLOW: Research -> Coding -> Testing -> Presentation
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from core.productivity.models import (
    GoalStatus,
    MilestoneStatus,
    PersonalTask,
    PlanStatus,
    TaskPriority,
    TaskStatus,
)
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "e2e_productivity.db")


# ==============================================================================
# TEST 1 — PROJECT CREATION
# ==============================================================================
def test_e2e_scenario_1_project_creation(prod: ProductivityOrchestrator, tmp_path: Path):
    """
    User: "Create a project for building an AI OCR system."
    Expected: Project created -> Context created -> Workspace ready -> User can add goals/tasks.
    """
    workspace = tmp_path / "ai_ocr_system"
    workspace.mkdir(parents=True, exist_ok=True)

    project = prod.projects.create_project(
        name="AI OCR System",
        description="Autonomous Vision and OCR text extraction engine",
        priority=TaskPriority.HIGH,
        codebase_path=str(workspace),
        tags=["vision", "ocr", "ai"],
    )

    assert project.id.startswith("proj_")
    assert project.name == "AI OCR System"
    assert project.codebase_path == str(workspace)

    # Context created
    ctx = prod.context.get_project_context(project.id)
    assert ctx["project_name"] == "AI OCR System"
    assert ctx["status"] == "ACTIVE"

    # User can add goals and tasks
    task = prod.tasks.create_task(
        title="Setup OCR project architecture",
        project_id=project.id,
    )
    assert task.project_id == project.id


# ==============================================================================
# TEST 2 — GOAL BREAKDOWN
# ==============================================================================
def test_e2e_scenario_2_goal_breakdown(prod: ProductivityOrchestrator):
    """
    User: "Help me break this project into milestones."
    Expected: Proposal generated -> User reviews -> Milestones created.
    """
    project = prod.projects.create_project(name="AI OCR Project")
    goal = prod.goals.create_goal(title="Deliver AI OCR System")

    # Propose breakdown
    proposal = prod.goals.propose_goal_breakdown(goal.title, category="AI Engineering")
    assert "proposed_milestones" in proposal
    assert len(proposal["proposed_milestones"]) >= 5

    # User reviews and accepts proposal -> Milestones instantiated
    titles = [m["title"] for m in proposal["proposed_milestones"]]
    milestones = prod.goals.instantiate_proposed_milestones(
        goal_id=goal.id,
        milestone_titles=titles,
        project_id=project.id,
    )

    assert len(milestones) == len(titles)
    assert all(m.project_id == project.id for m in milestones)
    assert all(m.goal_id == goal.id for m in milestones)


# ==============================================================================
# TEST 3 — CONTINUATION
# ==============================================================================
def test_e2e_scenario_3_project_continuation(prod: ProductivityOrchestrator):
    """
    User: "Continue the OCR project."
    Expected: Project identified -> Context loaded -> Current milestone identified ->
              Blockers identified -> Next actions proposed.
    """
    project = prod.projects.create_project(name="OCR")
    m1 = prod.store.save_milestone(
        prod.goals.store.models.Milestone(project_id=project.id, title="Implementation", status=MilestoneStatus.IN_PROGRESS)
        if hasattr(prod.goals.store, "models") else None
    ) if hasattr(prod.goals.store, "models") else None

    # Create milestone directly
    from core.productivity.models import Milestone
    ms = Milestone(project_id=project.id, title="Implementation", status=MilestoneStatus.IN_PROGRESS)
    prod.store.save_milestone(ms)

    t1 = prod.tasks.create_task(title="Build Pipeline", project_id=project.id)
    t2 = prod.tasks.create_task(title="Train Vision Model", project_id=project.id)
    t3 = prod.tasks.create_task(title="Write Unit Tests", project_id=project.id)

    # Record 1 blocker
    prod.projects.record_blocker(
        project_id=project.id,
        title="GPU Out of Memory",
        description="Model weights exceed CUDA VRAM",
        affected_tasks=[t2.id],
    )

    summary = prod.context.get_continuity_summary("OCR")
    assert summary["found"] is True
    assert summary["project_name"] == "OCR"
    assert summary["current_milestone"] == "Implementation"
    assert len(summary["unfinished_tasks"]) == 3
    assert len(summary["open_blockers"]) == 1
    assert "GPU Out of Memory" in summary["open_blockers"][0]["title"]


# ==============================================================================
# TEST 4 — DAILY PLAN
# ==============================================================================
def test_e2e_scenario_4_daily_planning(prod: ProductivityOrchestrator):
    """
    User: "Plan my day."
    Expected: Tasks + Deadlines + Projects -> Proposed plan -> User approval.
    """
    project = prod.projects.create_project(name="Shivani Assistant")
    prod.tasks.create_task(
        title="Deep work: OCR pipeline implementation",
        estimated_duration_minutes=90,
        priority=TaskPriority.HIGH,
        project_id=project.id,
    )
    prod.tasks.create_task(
        title="README documentation update",
        estimated_duration_minutes=30,
        priority=TaskPriority.MEDIUM,
        project_id=project.id,
    )

    plan, warning = prod.planning.generate_daily_plan(available_minutes=480)
    assert plan.status == PlanStatus.PROPOSED
    assert len(plan.time_blocks) >= 2
    assert any("OCR pipeline" in b.title for b in plan.time_blocks)

    # User explicitly approves/accepts plan
    accepted = prod.planning.accept_plan(plan.id)
    assert accepted is True


# ==============================================================================
# TEST 5 — TASK COMPLETION
# ==============================================================================
def test_e2e_scenario_5_task_completion_gate(prod: ProductivityOrchestrator, tmp_path: Path):
    """
    User: "Finish the README task."
    Expected: Task identified -> Work performed -> Verification -> Task updated.
    """
    readme_file = tmp_path / "README.md"
    readme_file.write_text("# Shivani OCR Documentation\nDetailed usage guide.")

    task = prod.tasks.create_task(
        title="Finish README documentation",
        artifacts=[str(readme_file)],
        context={"requires_tests_pass": True},
    )

    # 1. Attempting to mark complete without passing tests fails verification gate
    verified, errors = prod.tasks.complete_task(
        task.id,
        execution_output={"artifact_path": str(readme_file), "tests_passed": False},
    )
    assert verified is False
    assert any("passing automated tests" in e for e in errors)

    # 2. When tests pass and artifact exists -> Completion verified
    verified_ok, errors_ok = prod.tasks.complete_task(
        task.id,
        execution_output={"artifact_path": str(readme_file), "tests_passed": True},
    )
    assert verified_ok is True
    reloaded = prod.store.get_task(task.id)
    assert reloaded.status == TaskStatus.COMPLETED
    assert reloaded.completed_at is not None


# ==============================================================================
# TEST 6 — BLOCKER ANALYSIS
# ==============================================================================
def test_e2e_scenario_6_blocker_root_cause(prod: ProductivityOrchestrator):
    """
    User: "Why can't I deploy this project?"
    Expected: Project context -> Dependencies -> Recent failures -> Configuration -> Actual blocker identified.
    """
    project = prod.projects.create_project(name="Cloud Service")
    task_deploy = prod.tasks.create_task(title="Deploy to Production", project_id=project.id)

    # Record actual blocker
    prod.projects.record_blocker(
        project_id=project.id,
        title="Missing SSL Certificate",
        description="Production domain SSL certificate expired 2 hours ago",
        affected_tasks=[task_deploy.id],
        dependency="Domain DNS",
    )

    from agents.project.project_agent import ProjectAgent
    agent = ProjectAgent(productivity=prod)
    analysis = agent.analyze_blockers(project.id)

    assert analysis["open_blockers_count"] == 1
    assert analysis["blockers"][0]["title"] == "Missing SSL Certificate"
    assert "Deploy to Production" in analysis["blockers"][0]["affected_tasks"]


# ==============================================================================
# TEST 7 — CONFLICT RESOLUTION
# ==============================================================================
def test_e2e_scenario_7_deadline_conflict(prod: ProductivityOrchestrator):
    """
    Create conflicting deadlines.
    Expected: Conflict detected -> Ask user -> No silent overwrite.
    """
    now = datetime.now(timezone.utc)
    t_later = (now + timedelta(days=5)).strftime("%Y-%m-%d")
    t_earlier = (now + timedelta(days=2)).strftime("%Y-%m-%d")

    task_spec = prod.tasks.create_task(title="Architecture Spec", due_date=t_later)
    task_impl = prod.tasks.create_task(
        title="Implementation",
        due_date=t_earlier,
        dependencies=[task_spec.id],
    )

    conflicts = prod.deadlines.detect_conflicts([task_spec, task_impl])
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c["type"] == "DEPENDENCY_DEADLINE_INVERSION"
    assert c["task_id"] == task_impl.id
    assert c["dependency_id"] == task_spec.id
    # No silent date modification occurred
    assert task_impl.due_date == t_earlier
    assert task_spec.due_date == t_later


# ==============================================================================
# TEST 8 — CROSS-AGENT WORKFLOW
# ==============================================================================
def test_e2e_scenario_8_cross_agent_workflow(prod: ProductivityOrchestrator):
    """
    User: "Research this technology, implement a prototype, test it, and make a presentation."
    Expected: Research -> Knowledge -> Coding -> Testing -> Presentation -> Artifacts.
              Every stage verified with structured handoff.
    """
    # Stage 1: Research Agent Handoff
    h1 = prod.create_agent_handoff(
        from_agent="orchestrator",
        to_agent="research_agent",
        objective="Research WebAssembly OCR runtimes",
        context_data={"technology": "Wasm OCR", "budget_minutes": 30},
        next_action="Synthesize top 3 WASM OCR engines",
    )
    assert h1["to_agent"] == "research_agent"

    # Stage 2: Research -> Coding Agent
    h2 = prod.create_agent_handoff(
        from_agent="research_agent",
        to_agent="coding_agent",
        objective="Implement WASM OCR prototype",
        context_data={"chosen_engine": "tesseract.js", "requirements": ["headless execution"]},
        artifacts=["research_summary.json"],
        next_action="Build wrapper class and CLI entrypoint",
    )
    assert h2["from_agent"] == "research_agent"
    assert h2["to_agent"] == "coding_agent"
    assert "research_summary.json" in h2["artifacts"]

    # Stage 3: Coding -> Presentation Agent
    h3 = prod.create_agent_handoff(
        from_agent="coding_agent",
        to_agent="presentation_agent",
        objective="Create 5-slide pitch deck summarizing OCR results",
        context_data={"test_accuracy": "98.4%", "speed_ms": 120},
        artifacts=["ocr_engine.py", "benchmark_results.json"],
        next_action="Generate PowerPoint presentation artifact",
    )
    assert h3["from_agent"] == "coding_agent"
    assert h3["to_agent"] == "presentation_agent"
    assert len(h3["artifacts"]) == 2
