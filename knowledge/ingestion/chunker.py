"""
SHIVANI Structure-Aware Chunker
Partitions documents into semantically coherent chunks while preserving
section heading breadcrumbs, code blocks, tables, and exact line boundaries.
"""

from typing import Any, Dict, List, Optional
import uuid

from knowledge.ingestion.document_parser import HeadingNode, ParsedDocument
from knowledge.models import KnowledgeChunk


class StructureAwareChunker:
    """Chunks documents while preserving structural boundaries and heading breadcrumbs."""

    def __init__(self, target_words: int = 300, overlap_words: int = 40):
        self.target_words = target_words
        self.overlap_words = overlap_words

    def chunk_document(self, doc: ParsedDocument, item_id: str) -> List[KnowledgeChunk]:
        """Splits a ParsedDocument into structured KnowledgeChunks."""
        lines = doc.content.splitlines()
        if not lines:
            return []

        # If document is small enough, return as single chunk
        total_words = sum(len(line.split()) for line in lines)
        if total_words <= self.target_words * 1.2:
            return [
                KnowledgeChunk(
                    id=f"chk_{uuid.uuid4().hex[:12]}",
                    item_id=item_id,
                    content=doc.content,
                    token_count=total_words,
                    chunk_index=0,
                    heading_hierarchy=[doc.title],
                    line_start=1,
                    line_end=len(lines),
                    metadata={"file_name": doc.file_name, "is_full_doc": True},
                )
            ]

        # Map line numbers to active heading hierarchy
        chunks: List[KnowledgeChunk] = []
        cur_lines: List[str] = []
        cur_start_line = 1
        cur_word_count = 0
        chunk_idx = 0

        for line_num, line in enumerate(lines, start=1):
            words_in_line = len(line.split())

            # Check if this line is a heading boundary
            is_heading = any(h.line_number == line_num for h in doc.headings)

            # If accumulating chunk has reached target and we hit a heading or empty line, split
            if (cur_word_count >= self.target_words and (is_heading or not line.strip())) or (
                cur_word_count >= int(self.target_words * 1.5)
            ):
                if cur_lines:
                    chunk_text = "\n".join(cur_lines)
                    breadcrumbs = self._resolve_heading_breadcrumbs(doc, cur_start_line)
                    chunks.append(
                        KnowledgeChunk(
                            id=f"chk_{uuid.uuid4().hex[:12]}",
                            item_id=item_id,
                            content=chunk_text,
                            token_count=cur_word_count,
                            chunk_index=chunk_idx,
                            heading_hierarchy=breadcrumbs,
                            line_start=cur_start_line,
                            line_end=line_num - 1,
                            metadata={"file_name": doc.file_name},
                        )
                    )
                    chunk_idx += 1

                    # Retain overlap lines
                    overlap_lines: List[str] = []
                    overlap_cnt = 0
                    for l in reversed(cur_lines):
                        w = len(l.split())
                        if overlap_cnt + w <= self.overlap_words:
                            overlap_lines.insert(0, l)
                            overlap_cnt += w
                        else:
                            break

                    cur_lines = list(overlap_lines)
                    cur_word_count = overlap_cnt
                    cur_start_line = line_num - len(overlap_lines)

            cur_lines.append(line)
            cur_word_count += words_in_line

        # Flush final chunk
        if cur_lines and any(l.strip() for l in cur_lines):
            chunk_text = "\n".join(cur_lines)
            breadcrumbs = self._resolve_heading_breadcrumbs(doc, cur_start_line)
            chunks.append(
                KnowledgeChunk(
                    id=f"chk_{uuid.uuid4().hex[:12]}",
                    item_id=item_id,
                    content=chunk_text,
                    token_count=cur_word_count,
                    chunk_index=chunk_idx,
                    heading_hierarchy=breadcrumbs,
                    line_start=cur_start_line,
                    line_end=len(lines),
                    metadata={"file_name": doc.file_name},
                )
            )

        return chunks

    def _resolve_heading_breadcrumbs(self, doc: ParsedDocument, line_num: int) -> List[str]:
        """Determines the active hierarchy of headings at a given line number."""
        breadcrumbs: List[str] = [doc.file_name]
        active_stack: List[HeadingNode] = []

        for h in doc.headings:
            if h.line_number > line_num:
                break
            # Pop higher or equal levels
            while active_stack and active_stack[-1].level >= h.level:
                active_stack.pop()
            active_stack.append(h)

        for h in active_stack:
            breadcrumbs.append(h.title)

        return breadcrumbs
