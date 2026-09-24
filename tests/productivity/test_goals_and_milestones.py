"""
Unit tests for Phase 16 Goals, Milestones, and Progress Engine.
"""

from pathlib import Path
import pytest
from core.productivity.models import GoalStatus, MilestoneStatus, TaskPriority, TaskStatus
from core.productivity.orchestrator import ProductivityOrchestrator


@pytest.fixture
def temp_prod(tmp_path: Path):
    return ProductivityOrchestrator(db_path=tmp_path / "test_prod.db")


def test_goal_creation_and_listing(temp_prod: ProductivityOrchestrator):
    goal = temp_prod.goals.create_goal(
        title="Master Autonomous Agent Systems",
        description="Complete all 16 phases of personal AI assistant",
        category="Learning",
        priority=TaskPriority.HIGH,
        target_date="2026-12-31",
    )
    assert goal.id.startswith("goal_")
    assert goal.title == "Master Autonomous Agent Systems"
    assert goal.progress == 0.0

    listed = temp_prod.goals.list_goals()
    assert len(listed) == 1
    assert listed[0].id == goal.id


def test_goal_milestone_breakdown_proposal(temp_prod: ProductivityOrchestrator):
    proposal = temp_prod.goals.propose_goal_breakdown("Build AI Research Project")
    assert "proposed_milestones" in proposal
    assert len(proposal["proposed_milestones"]) >= 5
    first_ms = proposal["proposed_milestones"][0]
    assert "Research" in first_ms["title"] or "Literature" in first_ms["title"] or "Requirements" in first_ms["title"]

    # Instantiate proposed milestones
    goal = temp_prod.goals.create_goal(title="AI Research Project")
    titles = [m["title"] for m in proposal["proposed_milestones"]]
    instantiated = temp_prod.goals.instantiate_proposed_milestones(goal.id, titles)
    assert len(instantiated) == len(titles)
    # Check dependencies are chained
    assert instantiated[1].dependencies == [instantiated[0].id]


def test_goal_progress_rollup(temp_prod: ProductivityOrchestrator):
    goal = temp_prod.goals.create_goal(title="Launch Product")
    m1 = temp_prod.store.save_milestone(
        temp_prod.store.models.Milestone(goal_id=goal.id, title="M1", status=MilestoneStatus.COMPLETED)
        if hasattr(temp_prod.store, "models") else None
    ) if hasattr(temp_prod.store, "models") else None

    # Using milestone instantiation
    milestones = temp_prod.goals.instantiate_proposed_milestones(goal.id, ["M1", "M2"])
    assert len(milestones) == 2

    # Initially 0%
    goal = temp_prod.goals.update_goal_progress(goal.id)
    assert goal.progress == 0.0

    # Mark M1 complete
    milestones[0].status = MilestoneStatus.COMPLETED
    temp_prod.store.save_milestone(milestones[0])

    goal = temp_prod.goals.update_goal_progress(goal.id)
    assert goal.progress == 0.5

    # Mark M2 complete -> 100% and goal auto-completes
    milestones[1].status = MilestoneStatus.COMPLETED
    temp_prod.store.save_milestone(milestones[1])

    goal = temp_prod.goals.update_goal_progress(goal.id)
    assert goal.progress == 1.0
    assert goal.status == GoalStatus.COMPLETED
