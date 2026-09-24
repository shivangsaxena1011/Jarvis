"""
Tests for TaskGraph, Cycle Detection, Topological Sorting, and Parallel Batching.
"""

import pytest
from planning.models import SubTaskPlan, SubTaskStatus
from planning.dependency_graph import TaskGraph


def test_task_graph_construction_and_ordering():
    graph = TaskGraph()

    t1 = SubTaskPlan(id="t1", title="Research", description="Do research", assigned_agent="research_agent")
    t2 = SubTaskPlan(id="t2", title="Report", description="Write report", assigned_agent="documentation_agent", dependencies=["t1"])
    t3 = SubTaskPlan(id="t3", title="Deck", description="Make slides", assigned_agent="presentation_agent", dependencies=["t2"])

    graph.add_node(t1)
    graph.add_node(t2)
    graph.add_node(t3)

    assert not graph.has_cycle()
    order = graph.topological_sort()
    assert order == ["t1", "t2", "t3"]


def test_task_graph_cycle_detection():
    graph = TaskGraph()

    t1 = SubTaskPlan(id="t1", title="Task 1", description="", assigned_agent="agent1")
    t2 = SubTaskPlan(id="t2", title="Task 2", description="", assigned_agent="agent2", dependencies=["t1"])

    graph.add_node(t1)
    graph.add_node(t2)
    # Introduce circular dependency: t1 depends on t2
    graph.add_edge("t2", "t1")

    assert graph.has_cycle()
    with pytest.raises(ValueError, match="circular dependencies"):
        graph.topological_sort()


def test_parallel_execution_batches():
    graph = TaskGraph()

    # Wave 1: Independent research on two topics
    r1 = SubTaskPlan(id="r1", title="Research Topic A", description="", assigned_agent="research_agent")
    r2 = SubTaskPlan(id="r2", title="Research Topic B", description="", assigned_agent="research_agent")

    # Wave 2: Synthesis combining both research outputs
    s1 = SubTaskPlan(id="s1", title="Synthesize", description="", assigned_agent="coding_agent", dependencies=["r1", "r2"])

    # Wave 3: Parallel outputs (Slides & Social Draft)
    p1 = SubTaskPlan(id="p1", title="Slides", description="", assigned_agent="presentation_agent", dependencies=["s1"])
    soc = SubTaskPlan(id="soc", title="Post", description="", assigned_agent="browser_agent", dependencies=["s1"])

    for node in [r1, r2, s1, p1, soc]:
        graph.add_node(node)

    batches = graph.get_parallel_execution_batches()
    assert len(batches) == 3

    # Batch 1 contains r1 and r2
    b1_ids = {n.subtask.id for n in batches[0]}
    assert b1_ids == {"r1", "r2"}

    # Batch 2 contains s1
    b2_ids = {n.subtask.id for n in batches[1]}
    assert b2_ids == {"s1"}

    # Batch 3 contains p1 and soc
    b3_ids = {n.subtask.id for n in batches[2]}
    assert b3_ids == {"p1", "soc"}


def test_ready_nodes_progression():
    graph = TaskGraph()

    t1 = SubTaskPlan(id="t1", title="Step 1", description="", assigned_agent="a1")
    t2 = SubTaskPlan(id="t2", title="Step 2", description="", assigned_agent="a2", dependencies=["t1"])

    graph.add_node(t1)
    graph.add_node(t2)

    # Initially only t1 is ready
    ready = graph.get_ready_nodes()
    assert len(ready) == 1
    assert ready[0].subtask.id == "t1"

    # Mark t1 completed
    graph.mark_completed("t1", {"data": "done"})

    # Now t2 is ready
    ready_after = graph.get_ready_nodes()
    assert len(ready_after) == 1
    assert ready_after[0].subtask.id == "t2"

    graph.mark_completed("t2")
    assert graph.is_completed() is True
