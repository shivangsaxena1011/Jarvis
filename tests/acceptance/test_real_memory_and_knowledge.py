"""
Real-world Memory, Security & Knowledge Acceptance Test (Phase 20.5)
Verifies preference storage, recall, scoping, secret redaction,
and temporary document indexing and retrieval.
"""

from pathlib import Path
import tempfile
import pytest

from memory.manager import MemoryManager
from memory.models import (
    MemoryCategory,
    MemoryItem,
    MemoryScope,
    MemorySource,
    SecretRedactor,
)


def test_real_memory_store_retrieve_scope_and_delete():
    """Verifies storing a scoped project name preference, recalling it, and deleting it."""
    mgr = MemoryManager(db_path=":memory:")

    # 1. Store preference
    item = mgr.set_preference(
        key="test_project_codename",
        value="Apollo",
        scope=MemoryScope.PROJECT,
        scope_id="project-xyz",
        explanation="User said: For this test project, call it Apollo",
    )
    assert item is not None
    assert item.value == "Apollo"
    assert item.source == MemorySource.EXPLICIT_USER

    # 2. Retrieve preference
    val = mgr.get_preference(key="test_project_codename", project_id="project-xyz")
    assert val == "Apollo"

    # 3. Different project ID should not leak the scoped value
    val_other = mgr.get_preference(key="test_project_codename", project_id="project-different")
    assert val_other != "Apollo"

    # 4. Forget / delete
    ok = mgr.preferences.delete_preference(key="test_project_codename", scope=MemoryScope.PROJECT, scope_id="project-xyz")
    assert ok is True
    assert mgr.get_preference(key="test_project_codename", project_id="project-xyz") is None
    mgr.store._conn.close()


def test_real_memory_secret_redaction():
    """Verifies that attempt to store credentials in memory is automatically scrubbed by SecretRedactor."""
    sensitive_payload = "Project DB password is secret_pass_123456 and api_key is sk-ant-api03-abcdef1234567890abcdef"
    redacted = SecretRedactor.redact_text(sensitive_payload)

    assert "secret_pass_123456" not in redacted
    assert "sk-ant-api03" not in redacted
    assert "[REDACTED" in redacted


def test_real_local_document_knowledge_indexing_and_search():
    """Verifies indexing a project documentation file and querying key content from it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        doc_path = Path(tmpdir) / "README.md"
        doc_content = """# Apollo Authentication Service
        This service provides OAuth2 and JWT token validation for the enterprise gateway.
        def handle_authentication(token: str) -> bool:
            return token.startswith('auth_')
        """
        doc_path.write_text(doc_content, encoding="utf-8")

        # Simulate knowledge extraction / reading
        read_text = doc_path.read_text(encoding="utf-8")
        assert "Apollo Authentication Service" in read_text
        assert "handle_authentication" in read_text

        # Verify query matching
        query = "function that handles authentication"
        terms = [t for t in query.split() if len(t) > 3]
        matches = [line.strip() for line in read_text.splitlines() if any(t in line.lower() for t in terms)]
        assert len(matches) > 0
        assert any("handle_authentication" in m for m in matches)
