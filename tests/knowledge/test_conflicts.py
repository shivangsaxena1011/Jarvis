"""
Unit Tests for Knowledge Conflict and Contradiction Detector
"""

from datetime import datetime, timedelta, timezone
import pytest
from knowledge.conflicts.detector import ConflictDetector
from knowledge.models import ConflictResolution, KnowledgeItem, KnowledgeType
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


@pytest.fixture
def detector():
    store = SQLiteKnowledgeStore(db_path=":memory:")
    det = ConflictDetector(store=store)
    yield det, store
    store.close()


def test_detect_database_conflict(detector):
    det, store = detector

    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=30)

    old_doc = KnowledgeItem(
        type=KnowledgeType.DOCUMENT,
        title="Initial Design Doc",
        content="Our primary database: MongoDB for unstructured logs.",
        created_at=old_time,
        updated_at=old_time,
    )
    new_doc = KnowledgeItem(
        type=KnowledgeType.DOCUMENT,
        title="Production PRD",
        content="Our primary database: PostgreSQL for relational integrity.",
        created_at=now,
        updated_at=now,
    )
    store.save_item(old_doc)
    store.save_item(new_doc)

    conflicts = det.detect_conflicts_between_items(old_doc, new_doc)
    assert len(conflicts) >= 1
    conf = conflicts[0]
    assert conf.topic == "Database Engine"
    assert "mongodb" in conf.statement_a.lower() or "mongodb" in conf.statement_b.lower()
    assert "postgresql" in conf.statement_a.lower() or "postgresql" in conf.statement_b.lower()

    # Resolve by recency
    resolution = det.resolve_by_recency(conf)
    assert resolution in (ConflictResolution.A_SUPERSEDES_B, ConflictResolution.B_SUPERSEDES_A)
    assert conf.resolution_status != ConflictResolution.UNRESOLVED
