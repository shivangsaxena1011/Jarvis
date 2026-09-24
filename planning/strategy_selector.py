"""
SHIVANI Strategy Selector.
Determines optimal execution strategy (SEQUENTIAL, PARALLEL, HIERARCHICAL, DRY_RUN) for a task plan.
"""

from planning.models import Goal, ExecutionStrategy
from planning.dependency_graph import TaskGraph


class StrategySelector:
    """Selects execution strategy based on graph topology and user constraints."""

    def select_strategy(self, goal: Goal, graph: TaskGraph) -> ExecutionStrategy:
        """Selects the best execution strategy for the goal and dependency graph."""
        q_lower = goal.objective.lower()

        # Check for dry-run or simulation requests
        if any(w in q_lower for w in ["dry run", "simulate", "test run", "what would you do"]):
            return ExecutionStrategy.DRY_RUN

        batches = graph.get_parallel_execution_batches()

        # If only 1 batch and multiple nodes, pure parallel execution
        if len(batches) == 1 and len(graph.nodes) > 1:
            return ExecutionStrategy.PARALLEL

        # If any batch has 2 or more nodes across a multi-batch graph, hierarchical parallel execution
        if any(len(b) > 1 for b in batches):
            return ExecutionStrategy.HIERARCHICAL

        # If every batch is single-node, sequential execution
        if all(len(b) == 1 for b in batches):
            return ExecutionStrategy.SEQUENTIAL

        return ExecutionStrategy.HIERARCHICAL
