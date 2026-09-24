"""
Tests for Strategy Selector and Constraint Engine.
"""

from planning.models import Goal, SubTaskPlan, ExecutionStrategy
from planning.dependency_graph import TaskGraph
from planning.strategy_selector import StrategySelector
from planning.constraint_engine import ConstraintEngine


def test_strategy_selector_hierarchical_and_parallel():
    selector = StrategySelector()

    # Parallel independent tasks
    g_par = Goal(raw_query="Parallel check", objective="Parallel check")
    graph_par = TaskGraph()
    graph_par.add_node(SubTaskPlan(id="p1", title="Task 1", description="", assigned_agent="a1"))
    graph_par.add_node(SubTaskPlan(id="p2", title="Task 2", description="", assigned_agent="a2"))

    strat_par = selector.select_strategy(g_par, graph_par)
    assert strat_par == ExecutionStrategy.PARALLEL

    # Multi-wave hierarchical graph
    g_hier = Goal(raw_query="Multi step", objective="Multi step")
    graph_hier = TaskGraph()
    t1 = SubTaskPlan(id="t1", title="Wave 1 A", description="", assigned_agent="a1")
    t2 = SubTaskPlan(id="t2", title="Wave 1 B", description="", assigned_agent="a2")
    t3 = SubTaskPlan(id="t3", title="Wave 2", description="", assigned_agent="a3", dependencies=["t1", "t2"])
    for t in [t1, t2, t3]:
        graph_hier.add_node(t)

    strat_hier = selector.select_strategy(g_hier, graph_hier)
    assert strat_hier == ExecutionStrategy.HIERARCHICAL

    # Dry run
    g_dry = Goal(raw_query="Dry run simulation", objective="Simulate research")
    strat_dry = selector.select_strategy(g_dry, graph_par)
    assert strat_dry == ExecutionStrategy.DRY_RUN


def test_constraint_engine_validates_limits():
    engine = ConstraintEngine(max_concurrency=2)

    goal = Goal(raw_query="Test", objective="Test")
    graph = TaskGraph()
    # 3 parallel tasks exceeds max_concurrency=2
    t1 = SubTaskPlan(id="t1", title="Task 1", description="", assigned_agent="a1")
    t2 = SubTaskPlan(id="t2", title="Task 2", description="", assigned_agent="a2")
    t3 = SubTaskPlan(id="t3", title="Task 3", description="", assigned_agent="a3")
    for t in [t1, t2, t3]:
        graph.add_node(t)

    is_valid, violations = engine.validate_constraints(goal, graph)
    assert is_valid is False
    assert any("exceeding max concurrency" in v for v in violations)


def test_constraint_engine_agent_availability():
    engine = ConstraintEngine()
    goal = Goal(raw_query="Phone action", objective="Phone action")
    graph = TaskGraph()
    graph.add_node(SubTaskPlan(id="p1", title="Tap phone", description="", assigned_agent="phone_agent"))

    # If phone_agent is not available
    is_valid, violations = engine.validate_constraints(goal, graph, available_agents=["computer_agent", "browser_agent"])
    assert is_valid is False
    assert any("phone_agent" in v for v in violations)
