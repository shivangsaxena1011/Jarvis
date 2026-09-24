"""
SHIVANI Knowledge Reranker
Refines hybrid retrieval rankings using exact lexical matching,
heading alignment, authority weighting, and recency decay.
"""

from typing import Any, Dict, List, Optional, Tuple
from knowledge.models import KnowledgeChunk


class KnowledgeReranker:
    """Post-retrieval reranker optimizing candidate chunk order for LLM synthesis."""

    def __init__(
        self,
        exact_match_weight: float = 0.20,
        heading_match_weight: float = 0.15,
        full_doc_penalty: float = 0.05,
    ):
        self.exact_match_weight = exact_match_weight
        self.heading_match_weight = heading_match_weight
        self.full_doc_penalty = full_doc_penalty

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[KnowledgeChunk, float]],
        limit: Optional[int] = None,
    ) -> List[Tuple[KnowledgeChunk, float]]:
        """Reranks candidate (KnowledgeChunk, score) pairs."""
        if not candidates or not query:
            return candidates

        q_lower = query.lower().strip()
        terms = [t for t in q_lower.split() if len(t) > 1]

        reranked: List[Tuple[KnowledgeChunk, float]] = []

        for chunk, initial_score in candidates:
            adjusted = initial_score
            c_text = chunk.content.lower()

            # Exact phrase matching bonus
            if q_lower in c_text:
                adjusted += self.exact_match_weight

            # Term density bonus
            matches = sum(1 for t in terms if t in c_text)
            term_ratio = matches / len(terms) if terms else 0.0
            adjusted += term_ratio * 0.10

            # Heading hierarchy relevance
            for h in chunk.heading_hierarchy:
                if any(t in h.lower() for t in terms):
                    adjusted += self.heading_match_weight
                    break

            # Slightly penalize unchunked full-doc fallbacks in favor of targeted chunks
            if chunk.metadata.get("is_full_doc"):
                adjusted -= self.full_doc_penalty

            reranked.append((chunk, round(max(adjusted, 0.0), 4)))

        reranked.sort(key=lambda x: x[1], reverse=True)
        if limit is not None:
            return reranked[:limit]
        return reranked
