"""
SHIVANI Dependency Graph & DAG Engine.
Provides TaskGraph with cycle detection, topological sorting, and parallel execution wave batching.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from planning.models import SubTaskPlan, TaskNode, SubTaskStatus


class TaskGraph:
    """Directed Acyclic Graph (DAG) coordinating task dependencies and parallel execution."""

    def __init__(self):
        self.nodes: Dict[str, TaskNode] = {}
        self.edges: List[Tuple[str, str]] = []  # List of (from_node_id, to_node_id)
        self.dependencies: Dict[str, Set[str]] = {}  # node_id -> set of dependency node_ids

    def add_node(self, subtask: SubTaskPlan) -> TaskNode:
        """Adds a subtask as a node in the graph."""
        if subtask.id in self.nodes:
            return self.nodes[subtask.id]

        node = TaskNode(
            subtask=subtask,
            predecessors=set(subtask.dependencies),
            successors=set(),
        )
        self.nodes[subtask.id] = node
        self.dependencies[subtask.id] = set(subtask.dependencies)

        # Wire up edges for existing dependencies
        for dep_id in subtask.dependencies:
            if dep_id in self.nodes:
                self.nodes[dep_id].successors.add(subtask.id)
                self.edges.append((dep_id, subtask.id))

        return node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Adds a directed dependency edge (from_id must complete before to_id)."""
        if from_id not in self.nodes or to_id not in self.nodes:
            raise KeyError(f"Both nodes ({from_id}, {to_id}) must exist before adding an edge.")

        self.edges.append((from_id, to_id))
        self.nodes[from_id].successors.add(to_id)
        self.nodes[to_id].predecessors.add(from_id)
        self.nodes[to_id].subtask.dependencies.append(from_id)
        self.dependencies[to_id].add(from_id)

    def has_cycle(self) -> bool:
        """Detects whether the task graph contains circular dependencies."""
        visited: Dict[str, int] = {nid: 0 for nid in self.nodes}  # 0=unvisited, 1=visiting, 2=visited

        def _dfs(node_id: str) -> bool:
            visited[node_id] = 1  # Mark in-progress
            for succ_id in self.nodes[node_id].successors:
                if visited.get(succ_id, 0) == 1:
                    return True  # Back-edge detected -> cycle!
                if visited.get(succ_id, 0) == 0:
                    if _dfs(succ_id):
                        return True
            visited[node_id] = 2  # Mark fully visited
            return False

        for nid in self.nodes:
            if visited[nid] == 0:
                if _dfs(nid):
                    return True
        return False

    def topological_sort(self) -> List[str]:
        """Returns ordered list of node IDs satisfying all dependency constraints."""
        if self.has_cycle():
            raise ValueError("Cannot perform topological sort on graph containing circular dependencies.")

        in_degree: Dict[str, int] = {nid: len(node.predecessors) for nid, node in self.nodes.items()}
        queue: List[str] = [nid for nid, deg in in_degree.items() if deg == 0]
        ordered: List[str] = []

        while queue:
            curr = queue.pop(0)
            ordered.append(curr)
            for succ in self.nodes[curr].successors:
                in_degree[succ] -= 1
                if in_degree[succ] == 0:
                    queue.append(succ)

        return ordered

    def get_parallel_execution_batches(self) -> List[List[TaskNode]]:
        """
        Groups nodes into parallel execution waves.
        All nodes within a batch can run concurrently because all dependencies are in earlier batches.
        """
        if self.has_cycle():
            raise ValueError("Cannot calculate parallel execution batches for cyclic graph.")

        in_degree: Dict[str, int] = {nid: len(node.predecessors) for nid, node in self.nodes.items()}
        batches: List[List[TaskNode]] = []
        remaining_nodes = set(self.nodes.keys())

        while remaining_nodes:
            # Nodes with in_degree == 0 among remaining
            current_batch_ids = [nid for nid in remaining_nodes if in_degree[nid] == 0]
            if not current_batch_ids:
                break  # Cycle safety

            current_batch = [self.nodes[nid] for nid in current_batch_ids]
            batches.append(current_batch)

            for nid in current_batch_ids:
                remaining_nodes.remove(nid)
                for succ in self.nodes[nid].successors:
                    if succ in remaining_nodes:
                        in_degree[succ] -= 1

        return batches

    def get_ready_nodes(self) -> List[TaskNode]:
        """Returns pending nodes whose predecessor dependencies have all completed."""
        ready: List[TaskNode] = []
        completed_ids = {
            nid for nid, node in self.nodes.items()
            if node.subtask.status in (SubTaskStatus.COMPLETED, SubTaskStatus.SKIPPED)
        }

        for node in self.nodes.values():
            if node.subtask.status == SubTaskStatus.PENDING:
                if all(p in completed_ids for p in node.predecessors):
                    ready.append(node)
        return ready

    def mark_completed(self, node_id: str, result_data: Optional[Dict[str, Any]] = None) -> None:
        """Marks node as successfully completed with output payload."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.subtask.status = SubTaskStatus.COMPLETED
            node.subtask.result_data = result_data or {}

    def mark_failed(self, node_id: str, error: str) -> None:
        """Marks node as failed with diagnostic error message."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.subtask.status = SubTaskStatus.FAILED
            node.subtask.error = error

    def is_completed(self) -> bool:
        """Checks if all nodes reached a terminal state without failure."""
        return all(
            node.subtask.status in (SubTaskStatus.COMPLETED, SubTaskStatus.SKIPPED)
            for node in self.nodes.values()
        )

    def is_failed(self) -> bool:
        """Checks if any node has failed."""
        return any(node.subtask.status == SubTaskStatus.FAILED for node in self.nodes.values())
