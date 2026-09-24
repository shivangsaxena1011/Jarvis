"""
Unit Tests for Hybrid Retrieval, Reranking, and Context Assembly
"""

import pytest
from knowledge.embeddings.provider import DeterministicLocalEmbeddingProvider
from knowledge.graph.graph import KnowledgeGraph
from knowledge.models import KnowledgeChunk, KnowledgeItem, KnowledgeType
from knowledge.retrieval.context_assembler import ContextAssembler
from knowledge.retrieval.hybrid_search import HybridSearchEngine
from knowledge.retrieval.reranker import KnowledgeReranker
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


@pytest.fixture
def retrieval_fixture():
    store = SQLiteKnowledgeStore(db_path=":memory:")
    embeddings = DeterministicLocalEmbeddingProvider()
    graph = KnowledgeGraph(store=store)

    # Ingest test items and chunks
    item1 = KnowledgeItem(id="doc_auth", type=KnowledgeType.DOCUMENT, title="Authentication Protocol", content="OAuth2 JWT details")
    item2 = KnowledgeItem(id="doc_db", type=KnowledgeType.DOCUMENT, title="Database Migration", content="Alembic and SQLite migrations")
    store.save_item(item1)
    store.save_item(item2)

    chunk1 = KnowledgeChunk(
        id="chk_auth",
        item_id=item1.id,
        content="JWT tokens are signed with HMAC-SHA256 and expire after 1 hour.",
        heading_hierarchy=["Auth Protocol", "Tokens"],
        line_start=10,
        line_end=20,
        metadata={"file_name": "auth.md"},
        embedding=embeddings.embed_text("JWT tokens are signed with HMAC-SHA256 and expire after 1 hour."),
    )
    chunk2 = KnowledgeChunk(
        id="chk_db",
        item_id=item2.id,
        content="Database migrations run automatically using Alembic during startup.",
        heading_hierarchy=["Database", "Migrations"],
        line_start=5,
        line_end=15,
        metadata={"file_name": "migrations.md"},
        embedding=embeddings.embed_text("Database migrations run automatically using Alembic during startup."),
    )
    store.save_chunks([chunk1, chunk2])

    engine = HybridSearchEngine(store=store, embedding_provider=embeddings, graph=graph)
    reranker = KnowledgeReranker()

    yield engine, reranker, store
    store.close()


def test_hybrid_search_and_reranking(retrieval_fixture):
    engine, reranker, store = retrieval_fixture

    # Search for token authentication
    results = engine.search(query="JWT tokens authentication", limit=5)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert top_chunk.id == "chk_auth"

    # Test reranker
    reranked = reranker.rerank(query="JWT tokens", candidates=results)
    assert reranked[0][0].id == "chk_auth"
    assert reranked[0][1] >= score  # Exact match bonus applied


def test_context_assembler(retrieval_fixture):
    engine, reranker, store = retrieval_fixture
    results = engine.search(query="Alembic database migrations", limit=5)

    assembled = ContextAssembler.assemble(results, max_characters=2000, include_citations=True)
    text = assembled["formatted_context"]

    assert "# Workspace Knowledge Context" in text
    assert "Alembic" in text
    assert "## Citations" in text
    assert len(assembled["citations"]) >= 1
