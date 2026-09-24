"""
SHIVANI Constraint Engine.
Enforces execution bounds, concurrency limits, permission policies, and agent availability.
"""

from typing import List, Tuple, Optional
from planning.models import Goal
from planning.dependency_graph import TaskGraph
from security.permissions.engine import RiskLevel


class ConstraintEngine:
    """Validates operational feasibility against system and user constraints."""

    def __init__(self, max_concurrency: int = 5):
        self.max_concurrency = max_concurrency

    def validate_constraints(
        self,
        goal: Goal,
        graph: TaskGraph,
        available_agents: Optional[List[str]] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Validates if graph can be safely executed under current constraints.
        Returns: (is_valid, list_of_violations)
        """
        violations: List[str] = []

        # 1. Concurrency limit check
        batches = graph.get_parallel_execution_batches()
        for i, batch in enumerate(batches):
            if len(batch) > self.max_concurrency:
                violations.append(
                    f"Batch {i + 1} contains {len(batch)} parallel tasks, exceeding max concurrency of {self.max_concurrency}."
                )

        # 2. Agent availability check
        if available_agents is not None:
            avail_set = set(available_agents)
            for node in graph.nodes.values():
                if node.subtask.assigned_agent not in avail_set:
                    violations.append(
                        f"Subtask '{node.subtask.title}' requires agent '{node.subtask.assigned_agent}', which is currently unavailable."
                    )

        # 3. Explicit user constraints check
        for constraint in goal.constraints:
            c_lower = constraint.lower()
            if "no social" in c_lower:
                for node in graph.nodes.values():
                    if node.subtask.stage == "DISTRIBUTION" or "linkedin" in node.subtask.title.lower():
                        violations.append("Constraint 'no social' violated by social posting subtask.")

        return (len(violations) == 0, violations)
