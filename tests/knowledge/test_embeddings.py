"""
Unit Tests for Embeddings Subsystem
"""

import pytest
from knowledge.embeddings.provider import (
    CloudEmbeddingProvider,
    DeterministicLocalEmbeddingProvider,
    cosine_similarity,
    get_embedding_provider,
)


def test_deterministic_embedding_properties():
    provider = DeterministicLocalEmbeddingProvider(dimension=384)
    assert provider.dimension == 384

    v1 = provider.embed_text("FastAPI backend with SQLite database")
    v2 = provider.embed_text("FastAPI backend with SQLite database")
    assert len(v1) == 384
    assert v1 == v2  # Perfectly deterministic

    v_diff = provider.embed_text("Frontend React components styling CSS")
    sim_same = cosine_similarity(v1, v2)
    sim_diff = cosine_similarity(v1, v_diff)

    assert sim_same == pytest.approx(1.0, abs=1e-4)
    assert sim_diff < 0.85  # Semantically distinct


def test_batch_embedding():
    provider = DeterministicLocalEmbeddingProvider()
    texts = ["Authentication and JWT tokens", "Database migrations and schemas", "Vector embeddings search"]
    batch = provider.embed_batch(texts)
    assert len(batch) == 3
    assert all(len(v) == 384 for v in batch)


def test_cloud_fallback():
    cloud = CloudEmbeddingProvider(dimension=384)
    vec = cloud.embed_text("Test fallback behavior")
    assert len(vec) == 384
