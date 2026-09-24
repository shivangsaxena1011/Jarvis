"""
Tests for Hierarchical Task Decomposition.
"""

from planning.goal_parser import GoalParser
from planning.task_decomposer import HierarchicalTaskDecomposer
from planning.models import SubTaskPlan


def test_decomposer_composite_productivity_workflow():
    parser = GoalParser()
    decomposer = HierarchicalTaskDecomposer()

    query = "Research AI agent frameworks, create a report, make a presentation and draft a LinkedIn post"
    goal = parser.parse(query)
    subtasks = decomposer.decompose(goal)

    assert len(subtasks) == 4
    stages = [st.stage for st in subtasks]
    assert stages == ["RESEARCH", "DOCUMENTATION", "PRESENTATION", "DISTRIBUTION"]

    agents = [st.assigned_agent for st in subtasks]
    assert "research_agent" in agents
    assert "documentation_agent" in agents
    assert "presentation_agent" in agents

    # Check dependency wiring: report depends on research
    report_subtask = next(st for st in subtasks if st.stage == "DOCUMENTATION")
    res_subtask = next(st for st in subtasks if st.stage == "RESEARCH")
    assert res_subtask.id in report_subtask.dependencies


def test_decomposer_coding_workflow():
    parser = GoalParser()
    decomposer = HierarchicalTaskDecomposer()

    query = "Find the login bug, implement the fix, and run the tests"
    goal = parser.parse(query)
    subtasks = decomposer.decompose(goal)

    assert len(subtasks) == 3
    stages = [st.stage for st in subtasks]
    assert stages == ["ANALYSIS", "IMPLEMENTATION", "TESTING"]
    assert all(st.assigned_agent == "coding_agent" for st in subtasks)

    # Check dependencies: testing depends on implementation, implementation depends on analysis
    patch_task = subtasks[1]
    test_task = subtasks[2]
    assert subtasks[0].id in patch_task.dependencies
    assert patch_task.id in test_task.dependencies


def test_decomposer_single_action():
    parser = GoalParser()
    decomposer = HierarchicalTaskDecomposer()

    goal = parser.parse("Open Google Chrome")
    subtasks = decomposer.decompose(goal)

    assert len(subtasks) == 1
    assert subtasks[0].assigned_agent in ("browser_agent", "computer_agent")
