"""
SHIVANI Provenance & Citation Generator
Ensures exact, line-accurate attribution for every generated claim.
"""

from typing import Any, Dict, List, Optional
from knowledge.models import Citation, KnowledgeChunk, Provenance


class ProvenanceEngine:
    """Manages provenance tracking and citation linking for generated responses."""

    @classmethod
    def create_citation(
        cls,
        claim: str,
        chunk: KnowledgeChunk,
        confidence: float = 1.0,
    ) -> Citation:
        """Constructs a Citation object from a KnowledgeChunk."""
        source_title = chunk.heading_hierarchy[0] if chunk.heading_hierarchy else "Document"
        source_uri = chunk.metadata.get("file_path", chunk.metadata.get("file_name", "unknown"))
        return Citation(
            claim=claim,
            source_id=chunk.item_id,
            source_title=source_title,
            source_uri=source_uri,
            snippet=chunk.content[:180].strip(),
            line_start=chunk.line_start,
            line_end=chunk.line_end,
            confidence=confidence,
        )

    @classmethod
    def format_citations_markdown(cls, citations: List[Citation]) -> str:
        """Formats a list of citations as markdown footnotes."""
        if not citations:
            return ""
        lines = ["\n### References & Citations"]
        for idx, cit in enumerate(citations, start=1):
            lines.append(cit.to_footnote(idx))
        return "\n".join(lines)
