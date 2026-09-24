"""
SHIVANI Context Assembler
Packs retrieved knowledge chunks into formatted, token-budgeted prompt contexts
with line-accurate citations and section hierarchies.
"""

from typing import Any, Dict, List, Optional, Tuple
from knowledge.models import Citation, KnowledgeChunk


class ContextAssembler:
    """Assembles prompt-ready context windows from retrieved knowledge chunks."""

    @classmethod
    def assemble(
        cls,
        chunks: List[Tuple[KnowledgeChunk, float]],
        max_characters: int = 6000,
        include_citations: bool = True,
    ) -> Dict[str, Any]:
        """
        Formats chunks into structured Markdown context with footnotes.
        Returns dict with 'formatted_context', 'citations', and 'total_chunks'.
        """
        if not chunks:
            return {
                "formatted_context": "No relevant workspace knowledge found.",
                "citations": [],
                "total_chunks": 0,
            }

        context_blocks: List[str] = []
        citations: List[Citation] = []
        accumulated_chars = 0

        for idx, (chunk, score) in enumerate(chunks, start=1):
            heading_path = " > ".join(chunk.heading_hierarchy) if chunk.heading_hierarchy else "Document"
            file_name = chunk.metadata.get("file_name", "workspace_doc")

            block_header = f"### [Source {idx}] {heading_path} (Lines {chunk.line_start}-{chunk.line_end})"
            block_content = chunk.content.strip()
            full_block = f"{block_header}\n```\n{block_content}\n```\n"

            if accumulated_chars + len(full_block) > max_characters and context_blocks:
                break

            context_blocks.append(full_block)
            accumulated_chars += len(full_block)

            citation = Citation(
                claim=f"Context from {heading_path}",
                source_id=chunk.item_id,
                source_title=file_name,
                source_uri=chunk.metadata.get("file_path", file_name),
                snippet=block_content[:150],
                line_start=chunk.line_start,
                line_end=chunk.line_end,
                confidence=min(max(score, 0.1), 1.0),
            )
            citations.append(citation)

        formatted_text = "# Workspace Knowledge Context\n\n" + "\n".join(context_blocks)

        if include_citations and citations:
            formatted_text += "\n## Citations\n"
            for i, cit in enumerate(citations, start=1):
                formatted_text += f"{cit.to_footnote(i)}\n"

        return {
            "formatted_context": formatted_text,
            "citations": citations,
            "total_chunks": len(context_blocks),
        }
