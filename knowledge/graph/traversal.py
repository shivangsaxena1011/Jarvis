"""
SHIVANI Graph Traversal Algorithms
Implements BFS, DFS, shortest path finding, and k-hop neighborhood expansion.
"""

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from knowledge.graph.graph import KnowledgeGraph
from knowledge.models import GraphEdge, RelationType


class GraphTraversal:
    """Graph search and traversal utilities."""

    @classmethod
    def bfs(
        cls,
        graph: KnowledgeGraph,
        start_node: str,
        max_depth: int = 3,
        relation_type: Optional[RelationType] = None,
    ) -> Dict[str, int]:
        """Breadth-first search returning node IDs and their hop distance from start."""
        distances: Dict[str, int] = {start_node: 0}
        queue: deque[Tuple[str, int]] = deque([(start_node, 0)])

        while queue:
            curr, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for neighbor, rel, _ in graph.get_neighbors(curr, direction="out", relation_type=relation_type):
                if neighbor not in distances:
                    distances[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))

        return distances

    @classmethod
    def dfs(
        cls,
        graph: KnowledgeGraph,
        start_node: str,
        max_depth: int = 3,
        relation_type: Optional[RelationType] = None,
    ) -> List[str]:
        """Depth-first search returning visited node IDs in traversal order."""
        visited: Set[str] = set()
        order: List[str] = []

        def _dfs_helper(node: str, depth: int):
            if depth > max_depth or node in visited:
                return
            visited.add(node)
            order.append(node)
            for neighbor, rel, _ in graph.get_neighbors(node, direction="out", relation_type=relation_type):
                _dfs_helper(neighbor, depth + 1)

        _dfs_helper(start_node, 0)
        return order

    @classmethod
    def shortest_path(
        cls,
        graph: KnowledgeGraph,
        source_id: str,
        target_id: str,
        relation_type: Optional[RelationType] = None,
    ) -> Optional[List[str]]:
        """Finds unweighted shortest path from source to target using BFS."""
        if source_id == target_id:
            return [source_id]

        queue: deque[List[str]] = deque([[source_id]])
        visited: Set[str] = {source_id}

        while queue:
            path = queue.popleft()
            curr = path[-1]

            for neighbor, rel, _ in graph.get_neighbors(curr, direction="out", relation_type=relation_type):
                if neighbor == target_id:
                    return path + [neighbor]
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(path + [neighbor])

        return None

    @classmethod
    def k_hop_subgraph(
        cls,
        graph: KnowledgeGraph,
        start_node: str,
        k: int = 2,
    ) -> Tuple[List[str], List[GraphEdge]]:
        """Extracts nodes and edges within k hops of start_node (bidirectional)."""
        visited_nodes: Set[str] = {start_node}
        queue: deque[Tuple[str, int]] = deque([(start_node, 0)])

        while queue:
            curr, depth = queue.popleft()
            if depth >= k:
                continue

            for neighbor, _, _ in graph.get_neighbors(curr, direction="both"):
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, depth + 1))

        # Collect internal edges between visited nodes
        subgraph_edges: List[GraphEdge] = []
        for n in visited_nodes:
            for edge in graph.get_edges(source_id=n):
                if edge.target_id in visited_nodes:
                    subgraph_edges.append(edge)

        return list(visited_nodes), subgraph_edges
