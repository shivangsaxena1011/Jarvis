"""
Tests for Priority Engine and Bottleneck Identification.
"""

from planning.models import SubTaskPlan
from planning.dependency_graph import TaskGraph
from planning.priority_engine import PriorityEngine
from security.permissions.engine import RiskLevel


def test_priority_engine_scores_critical_path():
    graph = TaskGraph()

    # Root task unblocking 3 downstream tasks
    root = SubTaskPlan(id="root", title="Core Data Extraction", description="", assigned_agent="research_agent")
    d1 = SubTaskPlan(id="d1", title="Branch 1", description="", assigned_agent="coding_agent", dependencies=["root"])
    d2 = SubTaskPlan(id="d2", title="Branch 2", description="", assigned_agent="documentation_agent", dependencies=["root"])
    d3 = SubTaskPlan(id="d3", title="Branch 3", description="", assigned_agent="presentation_agent", dependencies=["d1"])

    # Side task with 0 dependents
    side = SubTaskPlan(id="side", title="Independent Task", description="", assigned_agent="computer_agent")

    for t in [root, d1, d2, d3, side]:
        graph.add_node(t)

    engine = PriorityEngine()
    engine.calculate_priorities(graph)

    # Root has the highest downstream count (unblocks d1, d2, d3)
    assert graph.nodes["root"].priority > graph.nodes["side"].priority
    assert graph.nodes["root"].critical_path is True
    assert graph.nodes["side"].critical_path is False


def test_priority_engine_boosts_sensitive_approvals():
    graph = TaskGraph()

    safe_task = SubTaskPlan(id="safe", title="Safe Operation", description="", assigned_agent="computer_agent", risk_level=RiskLevel.SAFE)
    sens_task = SubTaskPlan(id="sens", title="Publish Post", description="", assigned_agent="browser_agent", risk_level=RiskLevel.SENSITIVE)

    graph.add_node(safe_task)
    graph.add_node(sens_task)

    engine = PriorityEngine()
    engine.calculate_priorities(graph)

    assert graph.nodes["sens"].priority > graph.nodes["safe"].priority
