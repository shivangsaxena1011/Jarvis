"""
Unit Tests for Directed Knowledge Graph Engine
"""

import pytest
from knowledge.graph.edges import GraphEdge, RelationType
from knowledge.graph.graph import KnowledgeGraph
from knowledge.graph.nodes import GraphNode
from knowledge.graph.queries import GraphQueries
from knowledge.graph.traversal import GraphTraversal
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


@pytest.fixture
def graph():
    store = SQLiteKnowledgeStore(db_path=":memory:")
    kg = KnowledgeGraph(store=store)
    yield kg
    store.close()


def test_graph_nodes_and_edges(graph):
    node1 = GraphNode(id="proj_1", name="Project 1")
    node2 = GraphNode(id="tech_fastapi", name="FastAPI")
    node3 = GraphNode(id="doc_arch", name="Architecture Doc")

    graph.add_node(node1)
    graph.add_node(node2)
    graph.add_node(node3)

    graph.add_edge(GraphEdge(source_id="proj_1", target_id="tech_fastapi", relation_type=RelationType.USES_TECHNOLOGY))
    graph.add_edge(GraphEdge(source_id="proj_1", target_id="doc_arch", relation_type=RelationType.DOCUMENTED_BY))

    assert graph.node_count == 3
    assert graph.edge_count == 2

    # Query neighbors
    techs = GraphQueries.get_technologies_used(graph, "proj_1")
    assert "Fastapi" in techs

    docs = GraphQueries.get_documentation_for_item(graph, "proj_1")
    assert "doc_arch" in docs


def test_graph_traversal(graph):
    # A -> B -> C -> D
    for src, dst in [("A", "B"), ("B", "C"), ("C", "D")]:
        graph.add_edge(GraphEdge(source_id=src, target_id=dst, relation_type=RelationType.CALLS))

    bfs_res = GraphTraversal.bfs(graph, "A", max_depth=3)
    assert bfs_res["A"] == 0
    assert bfs_res["B"] == 1
    assert bfs_res["C"] == 2
    assert bfs_res["D"] == 3

    path = GraphTraversal.shortest_path(graph, "A", "D")
    assert path == ["A", "B", "C", "D"]

    # k-hop subgraph around B
    sub_nodes, sub_edges = GraphTraversal.k_hop_subgraph(graph, "B", k=1)
    assert set(sub_nodes) == {"A", "B", "C"}
