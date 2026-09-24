"""
SHIVANI Directed Multigraph Engine
Represents interconnected knowledge relationships between files, symbols,
technologies, documentation, decisions, and tasks.
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from knowledge.graph.nodes import GraphNode
from knowledge.models import GraphEdge, RelationType
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class KnowledgeGraph:
    """Directed multigraph tracking semantic dependencies across the user workspace."""

    def __init__(self, store: Optional[SQLiteKnowledgeStore] = None):
        self.store = store
        self._nodes: Dict[str, GraphNode] = {}
        self._adj: Dict[str, List[GraphEdge]] = {}
        self._rev: Dict[str, List[GraphEdge]] = {}

        if self.store:
            self._load_from_store()

    def _load_from_store(self) -> None:
        """Loads existing graph edges from SQLite storage."""
        if not self.store:
            return
        edges = self.store.get_edges()
        for e in edges:
            self.add_edge(e, persist=False)

    def add_node(self, node: GraphNode) -> None:
        """Adds a node to the graph."""
        self._nodes[node.id] = node
        if node.id not in self._adj:
            self._adj[node.id] = []
        if node.id not in self._rev:
            self._rev[node.id] = []

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._nodes.get(node_id)

    def add_edge(self, edge: GraphEdge, persist: bool = True) -> None:
        """Adds a directed edge between two nodes."""
        if edge.source_id not in self._nodes:
            self.add_node(GraphNode(id=edge.source_id, name=edge.source_id))
        if edge.target_id not in self._nodes:
            self.add_node(GraphNode(id=edge.target_id, name=edge.target_id))

        if edge.source_id not in self._adj:
            self._adj[edge.source_id] = []
        if edge.target_id not in self._rev:
            self._rev[edge.target_id] = []

        # Remove duplicate edge if already present
        self._adj[edge.source_id] = [
            e for e in self._adj[edge.source_id]
            if not (e.target_id == edge.target_id and e.relation_type == edge.relation_type)
        ]
        self._rev[edge.target_id] = [
            e for e in self._rev[edge.target_id]
            if not (e.source_id == edge.source_id and e.relation_type == edge.relation_type)
        ]

        self._adj[edge.source_id].append(edge)
        self._rev[edge.target_id].append(edge)

        if persist and self.store:
            self.store.save_edges([edge])

    def get_edges(
        self,
        source_id: Optional[str] = None,
        target_id: Optional[str] = None,
        relation_type: Optional[RelationType] = None,
    ) -> List[GraphEdge]:
        """Returns matching edges."""
        results: List[GraphEdge] = []
        if source_id and source_id in self._adj:
            candidates = self._adj[source_id]
        elif target_id and target_id in self._rev:
            candidates = self._rev[target_id]
        else:
            candidates = [e for edges in self._adj.values() for e in edges]

        for e in candidates:
            if source_id and e.source_id != source_id:
                continue
            if target_id and e.target_id != target_id:
                continue
            if relation_type and e.relation_type != relation_type:
                continue
            results.append(e)

        return results

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "out",
        relation_type: Optional[RelationType] = None,
    ) -> List[Tuple[str, RelationType, float]]:
        """
        Returns list of (neighbor_id, relation_type, weight).
        direction can be 'out', 'in', or 'both'.
        """
        results: List[Tuple[str, RelationType, float]] = []

        if direction in ("out", "both") and node_id in self._adj:
            for e in self._adj[node_id]:
                if relation_type is None or e.relation_type == relation_type:
                    results.append((e.target_id, e.relation_type, e.weight))

        if direction in ("in", "both") and node_id in self._rev:
            for e in self._rev[node_id]:
                if relation_type is None or e.relation_type == relation_type:
                    results.append((e.source_id, e.relation_type, e.weight))

        return results

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._adj.values())
