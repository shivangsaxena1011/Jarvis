"""
Unit Tests for Ingestion Pipeline: Parsers, Table Extraction, and Structure-Aware Chunking
"""

from pathlib import Path
import pytest
from knowledge.ingestion.chunker import StructureAwareChunker
from knowledge.ingestion.document_parser import DocumentParser
from knowledge.ingestion.table_extractor import TableExtractor


def test_table_extractor_markdown():
    md = """
# Data Summary

| Feature | Status | Tier |
| --- | --- | --- |
| Hybrid Search | Implemented | High |
| Code Graph | Implemented | High |
"""
    tables = TableExtractor.extract_markdown_tables(md)
    assert len(tables) == 1
    assert tables[0]["headers"] == ["Feature", "Status", "Tier"]
    assert len(tables[0]["rows"]) == 2


def test_table_extractor_csv():
    csv_text = "Metric,Value\nAccuracy,98.5%\nLatency,12ms\n"
    md_table = TableExtractor.parse_csv_to_markdown(csv_text)
    assert "| Metric | Value |" in md_table
    assert "| Accuracy | 98.5% |" in md_table


def test_document_parser_markdown(tmp_path):
    doc_path = tmp_path / "ARCHITECTURE.md"
    content = """# SHIVANI Architecture

## Overview
SHIVANI is a personal autonomous AI computer assistant.

## Storage Subsystem
Uses local SQLite databases with WAL mode.

| Component | Engine |
| --- | --- |
| Memory | SQLite |
| Knowledge | SQLite |
"""
    doc_path.write_text(content, encoding="utf-8")

    parser = DocumentParser()
    parsed = parser.parse_file(str(doc_path))

    assert parsed.title == "SHIVANI Architecture"
    assert len(parsed.headings) == 3
    assert parsed.headings[0].title == "SHIVANI Architecture"
    assert parsed.headings[1].title == "Overview"
    assert parsed.headings[2].title == "Storage Subsystem"
    assert len(parsed.tables) == 1


def test_structure_aware_chunker(tmp_path):
    doc_path = tmp_path / "GUIDE.md"
    # Create long text to trigger chunking
    sections = []
    sections.append("# System Manual\n\nIntroduction to the system manual.\n")
    for i in range(1, 6):
        sections.append(f"## Module {i}\n" + ("Detailed description of component operations. " * 30) + "\n")
    content = "\n".join(sections)
    doc_path.write_text(content, encoding="utf-8")

    parser = DocumentParser()
    parsed = parser.parse_file(str(doc_path))

    chunker = StructureAwareChunker(target_words=100, overlap_words=20)
    chunks = chunker.chunk_document(parsed, item_id="kno_manual")

    assert len(chunks) > 1
    # Check that chunks contain heading breadcrumbs
    for c in chunks:
        assert len(c.heading_hierarchy) >= 1
        breadcrumbs_str = " ".join(c.heading_hierarchy)
        assert "System Manual" in breadcrumbs_str or "Module" in breadcrumbs_str
        assert c.line_start <= c.line_end
