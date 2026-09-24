"""
End-to-End Integration Tests for Phase 11 Planning and Orchestrator.
"""

import pytest
from planning.planner import AdvancedPlanner, get_advanced_planner
from planning.models import ExecutionStrategy
from core.orchestrator.orchestrator import Orchestrator


def test_advanced_planner_end_to_end_composite_goal():
    planner = get_advanced_planner()
    query = "Research latest AI agent frameworks, create a report, make a presentation and draft a LinkedIn post"

    goal, graph, strategy, validation = planner.create_plan_for_goal(query)

    assert goal.needs_clarification is False
    assert validation.is_valid is True
    assert strategy in (ExecutionStrategy.HIERARCHICAL, ExecutionStrategy.PARALLEL, ExecutionStrategy.SEQUENTIAL)
    assert len(graph.nodes) == 4

    # Verify critical path and priorities
    critical_nodes = [n for n in graph.nodes.values() if n.critical_path]
    assert len(critical_nodes) > 0


def test_advanced_planner_stops_on_clarification():
    planner = get_advanced_planner()
    goal, graph, strategy, validation = planner.create_plan_for_goal("Send this email")

    assert goal.needs_clarification is True
    assert validation.is_valid is False
    assert "clarification" in validation.errors[0]


@pytest.mark.asyncio
async def test_orchestrator_submit_autonomous_goal_clarification():
    orchestrator = Orchestrator()
    res = await orchestrator.submit_autonomous_goal("Send this email")

    assert res["status"] == "needs_clarification"
    assert "Who should receive" in res["question"]


@pytest.mark.asyncio
async def test_orchestrator_submit_autonomous_goal_success():
    orchestrator = Orchestrator()
    query = "Research AI agents and build presentation"

    res = await orchestrator.submit_autonomous_goal(query)
    assert res["status"] == "completed"
    assert "outputs" in res
    assert "graph" in res
