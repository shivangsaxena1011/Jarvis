"""
SHIVANI Priority Engine.
Computes execution urgency, dependency bottlenecks, and critical paths across TaskGraph nodes.
"""

from typing import Dict, Set
from planning.dependency_graph import TaskGraph
from security.permissions.engine import RiskLevel


class PriorityEngine:
    """Calculates dynamic priority and marks critical path bottlenecks."""

    def calculate_priorities(self, graph: TaskGraph) -> TaskGraph:
        """
        Assigns priority scores to nodes based on downstream dependency impact.
        Higher score = higher execution urgency.
        """
        # Calculate transitive downstream dependents for each node
        downstream_counts: Dict[str, int] = {}

        def get_all_successors(nid: str, visited: Set[str]) -> Set[str]:
            all_succs: Set[str] = set()
            for s in graph.nodes[nid].successors:
                if s not in visited:
                    visited.add(s)
                    all_succs.add(s)
                    all_succs.update(get_all_successors(s, visited))
            return all_succs

        for nid in graph.nodes:
            downstream = get_all_successors(nid, set())
            downstream_counts[nid] = len(downstream)

        # Max downstream count represents root of critical path
        max_downstream = max(downstream_counts.values()) if downstream_counts else 0

        for nid, node in graph.nodes.items():
            base_score = 10
            # Downstream unblock boost: each dependent task adds 10 points
            base_score += downstream_counts.get(nid, 0) * 10

            # Early approval warning boost: sensitive tasks requiring human approval get scheduled early
            if node.subtask.risk_level in (RiskLevel.SENSITIVE, RiskLevel.CRITICAL):
                base_score += 15

            # Critical path marker: nodes on the deepest dependency chain
            if max_downstream > 0 and downstream_counts.get(nid, 0) == max_downstream:
                node.critical_path = True
                base_score += 20
            elif node.predecessors and any(graph.nodes[p].critical_path for p in node.predecessors):
                # If predecessor was critical, this node continues the critical chain
                node.critical_path = True

            node.priority = base_score

        return graph
