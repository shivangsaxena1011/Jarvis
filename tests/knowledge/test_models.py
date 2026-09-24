"""
Unit Tests for SHIVANI Knowledge OS Data Models
"""

import pytest
from datetime import datetime, timezone
from knowledge.models import (
    Citation,
    CodeSymbol,
    CodeSymbolType,
    ConflictResolution,
    Entity,
    GraphEdge,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeType,
    ProjectProfile,
    Provenance,
    RelationType,
)


def test_knowledge_item_creation():
    prov = Provenance(source_file="docs/architecture.md", line_start=10, line_end=25)
    item = KnowledgeItem(
        type=KnowledgeType.DOCUMENT,
        title="Architecture Guide",
        content="System uses SQLite for local storage.",
        provenance=prov,
    )
    assert item.id.startswith("kno_")
    assert item.type == KnowledgeType.DOCUMENT
    assert item.provenance.line_start == 10
    assert item.provenance.line_end == 25


def test_chunk_and_citation():
    chunk = KnowledgeChunk(
        item_id="kno_123",
        content="The storage engine uses WAL mode for thread safety.",
        heading_hierarchy=["Storage", "WAL Mode"],
        line_start=45,
        line_end=52,
    )
    assert chunk.id.startswith("chk_")
    assert chunk.heading_hierarchy == ["Storage", "WAL Mode"]

    citation = Citation(
        claim="WAL mode ensures safety",
        source_id="kno_123",
        source_title="storage.py",
        source_uri="file:///c:/project/storage.py",
        snippet="uses WAL mode for thread safety",
        line_start=45,
        line_end=52,
        confidence=0.95,
    )
    fn = citation.to_footnote(1)
    assert "[^1]:" in fn
    assert "storage.py:45-52" in fn


def test_code_symbol_model():
    sym = CodeSymbol(
        file_path="core/storage.py",
        name="save_item",
        symbol_type=CodeSymbolType.METHOD,
        signature="def save_item(self, item: KnowledgeItem) -> KnowledgeItem",
        line_start=88,
        line_end=158,
        calls=["model_dump_json", "execute"],
        parent_symbol="SQLiteKnowledgeStore",
    )
    assert sym.id.startswith("sym_")
    assert sym.symbol_type == CodeSymbolType.METHOD
    assert "execute" in sym.calls


def test_conflict_model():
    conf = KnowledgeConflict(
        topic="Database Engine",
        item_a_id="kno_doc1",
        item_b_id="kno_doc2",
        statement_a="Database: PostgreSQL",
        statement_b="Database: SQLite",
        source_a="PRD.md",
        source_b="README.md",
        resolution_status=ConflictResolution.UNRESOLVED,
    )
    assert conf.id.startswith("cnf_")
    assert conf.resolution_status == ConflictResolution.UNRESOLVED
