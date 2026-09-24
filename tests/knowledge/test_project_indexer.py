"""
Unit Tests for Project Indexer and Project Context
"""

from pathlib import Path
import pytest
from knowledge.projects.project_context import ProjectContext
from knowledge.projects.project_indexer import ProjectIndexer
from knowledge.storage.sqlite_store import SQLiteKnowledgeStore


def test_discover_project(tmp_path):
    # Setup mock project structure
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text("""
[project]
name = "alpha_engine"
version = "2.1.0"
dependencies = [
    "fastapi>=0.115.0",
    "pytest>=8.0.0",
]
""", encoding="utf-8")

    readme = tmp_path / "README.md"
    readme.write_text("# Alpha Engine\nHigh performance computation engine.", encoding="utf-8")

    main_py = tmp_path / "main.py"
    main_py.write_text("print('start')", encoding="utf-8")

    store = SQLiteKnowledgeStore(db_path=":memory:")
    indexer = ProjectIndexer(store=store)
    profile = indexer.discover_project(str(tmp_path))

    assert profile.name == "alpha_engine"
    assert profile.version == "2.1.0"
    assert "Python" in profile.languages
    assert "FastAPI" in profile.frameworks
    assert "main.py" in profile.entry_points

    # Format for prompt
    context_str = ProjectContext.format_for_prompt(profile)
    assert "# Project: alpha_engine" in context_str
    assert "FastAPI" in context_str
    assert "main.py" in context_str

    store.close()
