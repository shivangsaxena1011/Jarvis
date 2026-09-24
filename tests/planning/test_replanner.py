"""
Tests for Dynamic Replanner and In-Flight Self-Correction.
"""

from planning.models import SubTaskPlan, SubTaskStatus
from planning.dependency_graph import TaskGraph
from planning.replanner import Replanner


def test_replanner_diagnoses_failure_types():
    replanner = Replanner()
    graph = TaskGraph()

    node = graph.add_node(SubTaskPlan(id="t1", title="Scrape Web", description="", assigned_agent="browser_agent"))

    trig_timeout = replanner.diagnose_failure(node, "Execution timed out after 60s")
    assert trig_timeout.error_type == "TIMEOUT"

    trig_visual = replanner.diagnose_failure(node, "Target button could not be found on screen via OCR")
    assert trig_visual.error_type == "VISUAL_MISMATCH"

    trig_tool = replanner.diagnose_failure(node, "Connection refused HTTP 403 Forbidden")
    assert trig_tool.error_type == "TOOL_FAILURE"

    trig_perm = replanner.diagnose_failure(node, "Permission denied: rejected by user policy")
    assert trig_perm.error_type == "PERMISSION_DENIED"


def test_replanner_synthesizes_fallback_and_rewires_dag():
    replanner = Replanner()
    graph = TaskGraph()

    # r1 -> report
    r1 = SubTaskPlan(id="r1", title="Scrape Academic Portal", description="", assigned_agent="research_agent")
    report = SubTaskPlan(id="rep", title="Synthesize Report", description="", assigned_agent="documentation_agent", dependencies=["r1"])

    graph.add_node(r1)
    graph.add_node(report)

    # Simulate failure on r1
    trigger = replanner.diagnose_failure(graph.nodes["r1"], "HTTP 403 Bot detection blocked scraper")
    revised_graph, can_continue = replanner.replan(graph, trigger)

    assert can_continue is True
    # r1 should be SKIPPED
    assert revised_graph.nodes["r1"].subtask.status == SubTaskStatus.SKIPPED

    # A fallback node was created and added to graph
    fallback_node = next(n for n in revised_graph.nodes.values() if "Fallback:" in n.subtask.title)
    assert fallback_node is not None

    # 'rep' node's predecessor should now be the fallback node, NOT r1
    assert fallback_node.subtask.id in revised_graph.nodes["rep"].predecessors
    assert "r1" not in revised_graph.nodes["rep"].predecessors


def test_replanner_handles_timeout_retry():
    replanner = Replanner()
    graph = TaskGraph()

    t1 = SubTaskPlan(id="t1", title="Long Query", description="", assigned_agent="a1", timeout_seconds=30.0, retry_policy={"max_retries": 2})
    graph.add_node(t1)

    trigger = replanner.diagnose_failure(graph.nodes["t1"], "Task timed out")
    revised_graph, can_continue = replanner.replan(graph, trigger)

    assert can_continue is True
    assert revised_graph.nodes["t1"].subtask.status == SubTaskStatus.PENDING
    assert revised_graph.nodes["t1"].subtask.timeout_seconds == 60.0  # Doubled
    assert revised_graph.nodes["t1"].subtask.retry_policy["max_retries"] == 1
