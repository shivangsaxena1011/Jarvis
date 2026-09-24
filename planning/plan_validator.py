"""
SHIVANI Plan Validator.
Verifies topological integrity, dependency contracts, and data wiring before execution starts.
"""

from planning.models import PlanValidationResult
from planning.dependency_graph import TaskGraph


class PlanValidator:
    """Performs static analysis on TaskGraphs to ensure execution soundness."""

    def validate(self, graph: TaskGraph) -> PlanValidationResult:
        """Validates graph structure, cycle freedom, and dependency completeness."""
        errors = []
        warnings = []

        # 1. Non-empty check
        if not graph.nodes:
            errors.append("TaskGraph contains no nodes.")
            return PlanValidationResult(is_valid=False, errors=errors)

        # 2. Cycle detection
        if graph.has_cycle():
            errors.append("TaskGraph contains a circular dependency cycle.")

        # 3. Dangling dependency check
        for nid, node in graph.nodes.items():
            for dep_id in node.subtask.dependencies:
                if dep_id not in graph.nodes:
                    errors.append(
                        f"Subtask '{node.subtask.title}' ({nid}) depends on non-existent node '{dep_id}'."
                    )

        # 4. Input-output dependency contract check
        for nid, node in graph.nodes.items():
            for input_key, source_node_id in node.subtask.inputs.items():
                if isinstance(source_node_id, str) and source_node_id.startswith("step_"):
                    if source_node_id not in graph.nodes:
                        errors.append(
                            f"Subtask '{node.subtask.title}' expects input '{input_key}' from missing node '{source_node_id}'."
                        )
                    elif source_node_id not in node.predecessors:
                        warnings.append(
                            f"Subtask '{node.subtask.title}' consumes data from '{source_node_id}' but does not list it as a formal predecessor."
                        )

        # 5. Agent assignment check
        for nid, node in graph.nodes.items():
            if not node.subtask.assigned_agent:
                errors.append(f"Subtask '{node.subtask.title}' ({nid}) has no assigned agent.")

        is_valid = len(errors) == 0
        return PlanValidationResult(is_valid=is_valid, errors=errors, warnings=warnings)
