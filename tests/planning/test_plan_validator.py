"""
Tests for Plan Validation and State Serialization.
"""

import tempfile, os
from planning.models import Goal, SubTaskPlan
from planning.dependency_graph import TaskGraph
from planning.plan_validator import PlanValidator
from planning.plan_serializer import PlanSerializer


def test_plan_validator_catches_dangling_dependencies():
    validator = PlanValidator()
    graph = TaskGraph()

    # Depends on ghost_node which is never added to graph
    t1 = SubTaskPlan(id="t1", title="Step 1", description="", assigned_agent="a1", dependencies=["ghost_node"])
    graph.add_node(t1)

    res = validator.validate(graph)
    assert res.is_valid is False
    assert any("ghost_node" in err for err in res.errors)


def test_plan_serializer_roundtrip():
    goal = Goal(raw_query="Prepare report", objective="Prepare report", desired_outputs=["report"])
    graph = TaskGraph()
    t1 = SubTaskPlan(id="t1", title="Research", description="Do research", assigned_agent="research_agent")
    t2 = SubTaskPlan(id="t2", title="Write", description="Write doc", assigned_agent="documentation_agent", dependencies=["t1"])
    graph.add_node(t1)
    graph.add_node(t2)

    temp_path = os.path.join(tempfile.gettempdir(), "test_serialized_plan.json")
    PlanSerializer.save_to_json(goal, graph, temp_path)

    assert os.path.exists(temp_path)

    loaded_goal, loaded_graph = PlanSerializer.load_from_json(temp_path)
    assert loaded_goal.objective == "Prepare report"
    assert len(loaded_graph.nodes) == 2
    assert "t1" in loaded_graph.nodes
    assert "t2" in loaded_graph.nodes
    assert "t1" in loaded_graph.nodes["t2"].predecessors
