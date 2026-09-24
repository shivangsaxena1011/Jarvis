"""
SHIVANI Hybrid Retrieval Engine
Combines BM25 keyword matching, dense vector semantic search, metadata filters,
and knowledge graph structural boosting using Reciprocal Rank Fusion (RRF).
"""

from typing import Any, Dict, List, Optional, Set, Tuple

from knowledge.embeddings.provider import EmbeddingProvider, get_embedding_provider
from knowledge.graph.graph import KnowledgeGraph
from knowledge.models import KnowledgeChunk, KnowledgeType
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


class HybridSearchEngine:
    """Multi-stage hybrid search engine with graph structural boosting."""

    def __init__(
        self,
        store: SQLiteKnowledgeStore,
        embedding_provider: Optional[EmbeddingProvider] = None,
        graph: Optional[KnowledgeGraph] = None,
    ):
        self.store = store
        self.embedding_provider = embedding_provider or get_embedding_provider()
        self.graph = graph

    def search(
        self,
        query: str,
        project_id: Optional[str] = None,
        types: Optional[List[KnowledgeType]] = None,
        limit: int = 10,
        alpha: float = 0.5,  # Weight for vector vs keyword (0.0 = pure keyword, 1.0 = pure vector)
        graph_boost_nodes: Optional[List[str]] = None,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """
        Executes hybrid retrieval:
        1. Keyword retrieval via BM25 score
        2. Vector retrieval via cosine similarity
        3. Reciprocal Rank Fusion & linear score combination
        4. Graph proximity boosting
        """
        if not query or not query.strip():
            return []

        # 1. Keyword search (retrieve 2x candidates)
        kw_candidates = self.store.search_chunks_keyword(
            query=query,
            project_id=project_id,
            types=types,
            limit=limit * 3,
        )

        # 2. Vector search (retrieve 2x candidates)
        query_vec = self.embedding_provider.embed_text(query)
        vec_candidates = self.store.search_chunks_vector(
            query_vector=query_vec,
            project_id=project_id,
            types=types,
            limit=limit * 3,
            min_similarity=0.0,
        )

        # 3. Fuse scores
        fused_scores: Dict[str, float] = {}
        chunk_map: Dict[str, KnowledgeChunk] = {}

        # Max score normalization for keyword results
        max_kw = max((s for _, s in kw_candidates), default=1.0) or 1.0
        for chunk, score in kw_candidates:
            chunk_map[chunk.id] = chunk
            norm_kw = score / max_kw
            fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + ((1.0 - alpha) * norm_kw)

        for chunk, score in vec_candidates:
            chunk_map[chunk.id] = chunk
            # Cosine similarity is already in [0, 1] for non-negative vectors
            fused_scores[chunk.id] = fused_scores.get(chunk.id, 0.0) + (alpha * max(score, 0.0))

        # 4. Graph structural boost
        if self.graph and graph_boost_nodes:
            boost_set: Set[str] = set()
            for b_node in graph_boost_nodes:
                boost_set.add(b_node)
                # Expand 1 hop
                for neighbor, _, _ in self.graph.get_neighbors(b_node, direction="both"):
                    boost_set.add(neighbor)

            for chunk_id, chunk in chunk_map.items():
                if chunk.item_id in boost_set or chunk.metadata.get("file_name") in boost_set:
                    fused_scores[chunk_id] = fused_scores.get(chunk_id, 0.0) * 1.25

        # Sort and return top candidates
        ranked = sorted(
            [(chunk_map[cid], round(score, 4)) for cid, score in fused_scores.items()],
            key=lambda x: x[1],
            reverse=True,
        )

        return ranked[:limit]
