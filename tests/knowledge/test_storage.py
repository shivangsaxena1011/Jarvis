"""
Unit Tests for SQLite Knowledge Storage Engine
"""

import pytest
from knowledge.models import (
    CodeSymbol,
    CodeSymbolType,
    ConflictResolution,
    GraphEdge,
    KnowledgeChunk,
    KnowledgeConflict,
    KnowledgeItem,
    KnowledgeType,
    RelationType,
)
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


@pytest.fixture
def store():
    db = SQLiteKnowledgeStore(db_path=":memory:")
    yield db
    db.close()


def test_save_and_get_item(store):
    item = KnowledgeItem(
        type=KnowledgeType.DOCUMENT,
        title="Project Architecture",
        content="This document details the multi-agent system architecture.",
        project_id="proj_jarvis",
    )
    saved = store.save_item(item)
    assert saved.id == item.id

    retrieved = store.get_item(item.id)
    assert retrieved is not None
    assert retrieved.title == "Project Architecture"
    assert retrieved.project_id == "proj_jarvis"


def test_save_chunks_and_keyword_search(store):
    item = KnowledgeItem(
        type=KnowledgeType.DOCUMENT,
        title="Database Schema",
        content="Contains table schemas.",
        project_id="proj_1",
    )
    store.save_item(item)

    chunk1 = KnowledgeChunk(
        item_id=item.id,
        content="The users table holds user accounts and authentication credentials.",
        heading_hierarchy=["Database", "Users Table"],
        line_start=1,
        line_end=10,
    )
    chunk2 = KnowledgeChunk(
        item_id=item.id,
        content="The orders table records customer purchases and transactions.",
        heading_hierarchy=["Database", "Orders Table"],
        line_start=11,
        line_end=20,
    )
    store.save_chunks([chunk1, chunk2])

    results = store.search_chunks_keyword("authentication accounts", project_id="proj_1")
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk.id == chunk1.id
    assert score > 0.0


def test_symbols_and_edges(store):
    sym = CodeSymbol(
        file_path="main.py",
        name="start_server",
        symbol_type=CodeSymbolType.FUNCTION,
        signature="def start_server(port: int = 8000)",
        calls=["uvicorn.run"],
    )
    store.save_symbols([sym])

    fetched = store.get_symbols(name="start_server")
    assert len(fetched) == 1
    assert fetched[0].name == "start_server"

    edge = GraphEdge(
        source_id=sym.id,
        target_id="mod_uvicorn",
        relation_type=RelationType.CALLS,
    )
    store.save_edges([edge])

    edges = store.get_edges(source_id=sym.id)
    assert len(edges) == 1
    assert edges[0].relation_type == RelationType.CALLS


def test_conflicts_crud(store):
    conf = KnowledgeConflict(
        topic="Database Engine",
        item_a_id="doc1",
        item_b_id="doc2",
        statement_a="PostgreSQL",
        statement_b="SQLite",
        source_a="PRD.md",
        source_b="README.md",
    )
    store.save_conflict(conf)

    conflicts = store.get_conflicts(topic="Database")
    assert len(conflicts) == 1
    assert conflicts[0].topic == "Database Engine"

    success = store.resolve_conflict(conf.id, ConflictResolution.A_SUPERSEDES_B, "Approved in meeting")
    assert success is True

    unresolved = store.get_conflicts(unresolved_only=True)
    assert len(unresolved) == 0
