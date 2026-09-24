"""
Unit Tests for Provenance Engine and Citations
"""

import pytest
from knowledge.citations.provenance import ProvenanceEngine
from knowledge.models import Citation, KnowledgeChunk


def test_create_and_format_citations():
    chunk = KnowledgeChunk(
        item_id="kno_auth",
        content="OAuth2 tokens require client_id and client_secret parameters.",
        heading_hierarchy=["Security", "OAuth2 Flow"],
        line_start=34,
        line_end=48,
        metadata={"file_path": "c:/repo/auth.py", "file_name": "auth.py"},
    )

    cit = ProvenanceEngine.create_citation(
        claim="OAuth2 tokens require client_id",
        chunk=chunk,
        confidence=0.92,
    )
    assert cit.line_start == 34
    assert cit.line_end == 48
    assert cit.source_uri == "c:/repo/auth.py"

    fn_markdown = ProvenanceEngine.format_citations_markdown([cit])
    assert "### References & Citations" in fn_markdown
    assert "[^1]: [Security:34-48]" in fn_markdown
