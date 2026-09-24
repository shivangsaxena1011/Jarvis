"""
End-to-End Tests for KnowledgeOS Unified Service Facade
"""

from pathlib import Path
import pytest
from knowledge.models import KnowledgeType
from knowledge.service import KnowledgeOS


@pytest.fixture
def kos(tmp_path):
    db_file = tmp_path / "knowledge_test.db"
    service = KnowledgeOS(db_path=str(db_file))
    yield service
    service.close()


def test_index_file_and_search(kos, tmp_path):
    sample_file = tmp_path / "SECURITY.md"
    content = """# Security Architecture

## Authentication
All requests must include a valid Bearer token header.

## Encryption
Data at rest is encrypted using AES-256-GCM.
"""
    sample_file.write_text(content, encoding="utf-8")

    item = kos.index_file(str(sample_file), project_id="proj_alpha")
    assert item is not None
    assert len(item.chunks) >= 1

    # Search for encryption
    res = kos.search(query="AES-256 encryption at rest", project_id="proj_alpha")
    assert res["results_count"] >= 1
    assert "AES-256" in res["context"]
    assert len(res["citations"]) >= 1


def test_index_directory(kos, tmp_path):
    # Setup multiple files
    (tmp_path / "README.md").write_text("# Test Project\nAn autonomous test workspace.", encoding="utf-8")
    (tmp_path / "main.py").write_text("def run():\n    return True\n", encoding="utf-8")

    res = kos.index_directory(str(tmp_path))
    assert res["files_indexed"] >= 2
    assert res["chunks_created"] >= 2

    stats = kos.get_stats()
    assert stats["total_items"] >= 2


def test_add_note_and_query_graph(kos):
    note = kos.add_note(
        title="Architecture Decision: Local SQLite",
        content="Decided to use SQLite with WAL mode rather than external Postgres daemon.",
        is_decision=True,
    )
    assert note.id.startswith("kno_")
    assert note.type == KnowledgeType.DECISION

    # Search finds the note
    search_res = kos.search("Postgres vs SQLite decision")
    assert "SQLite with WAL mode" in search_res["context"]
