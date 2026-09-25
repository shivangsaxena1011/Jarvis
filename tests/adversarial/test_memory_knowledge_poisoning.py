"""
Red-Team Adversarial Matrix: Memory & Knowledge Poisoning Defenses (Phase 20)
Verifies secret redaction in memory stores, provenance tracking, confidence bounds,
and resistance against injection in entity names and facts.
"""

from pathlib import Path
import tempfile
import pytest

from memory.models import (
    MemoryCategory,
    MemoryItem,
    MemoryScope,
    MemorySource,
    SecretRedactor,
)
from memory.manager import MemoryManager


def test_secret_redaction_in_memory_items():
    """Verifies that secrets (API keys, bearer tokens, passwords) are scrubbed before persistence."""
    leaked_text = "My secret token is ghp_123456789012345678901234567890123456 and api_key='sk-abcdefghijklmnopqrstuvwxyz12345'"
    redacted = SecretRedactor.redact_text(leaked_text)

    assert "ghp_123456789012345678901234567890123456" not in redacted
    assert "sk-abcdefghijklmnopqrstuvwxyz12345" not in redacted
    assert "[REDACTED_SECRET]" in redacted or "[REDACTED" in redacted


def test_memory_confidence_and_provenance_validation():
    """Verifies that memory items track provenance and reject out-of-bounds confidence values."""
    # Valid explicit user memory
    item = MemoryItem(
        category=MemoryCategory.USER_PREFERENCE,
        scope=MemoryScope.GLOBAL,
        key="editor",
        value="neovim",
        confidence=1.0,
        source=MemorySource.EXPLICIT_USER,
    )
    assert item.confidence == 1.0
    assert item.source == MemorySource.EXPLICIT_USER

    # Confidence must be bounded between 0.0 and 1.0
    with pytest.raises(Exception):
        MemoryItem(
            category=MemoryCategory.USER_PREFERENCE,
            key="editor",
            value="emacs",
            confidence=1.5, # Out of range
            source=MemorySource.INFERRED,
        )


def test_memory_sql_injection_resilience():
    """Verifies that malicious SQL tokens in memory keys or values do not cause syntax errors or schema corruption."""
    mgr = MemoryManager(db_path=":memory:")

    sql_injection_payload = "'; DROP TABLE memories; --"
    mgr.remember(
        key=sql_injection_payload,
        value={"data": "safe_payload", "attack": sql_injection_payload},
        category=MemoryCategory.CONTEXT,
        source=MemorySource.INFERRED,
    )

    # Retrieve and verify table wasn't dropped
    recalled = mgr.recall(sql_injection_payload)
    assert recalled is not None
    assert recalled["attack"] == sql_injection_payload

    # Verify normal operation continues
    mgr.remember(key="normal_key", value="normal_value")
    assert mgr.recall("normal_key") == "normal_value"
    mgr.store._conn.close()
