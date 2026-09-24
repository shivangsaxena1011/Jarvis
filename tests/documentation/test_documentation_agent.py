"""
Unit & Integration Tests for SHIVANI Documentation Agent.
Tests README generation, OpenAPI route extraction, architecture docs, and registered tools.
"""

import pytest
from pathlib import Path
from agents.documentation.agent import DocumentationAgent
from core.artifacts.manager import ArtifactManager
from tools.documentation import (
    DocumentationGenerateReadmeTool,
    DocumentationGenerateApiDocsTool,
    DocumentationGenerateArchDocTool,
)


@pytest.fixture
def sample_api_project(tmp_path):
    proj_dir = tmp_path / "micro_service"
    proj_dir.mkdir()

    (proj_dir / "pyproject.toml").write_text(
        '[project]\nname = "micro-service"\nversion = "0.1.0"\ndependencies = ["fastapi", "uvicorn"]\n',
        encoding="utf-8"
    )

    api_code = (
        'from fastapi import FastAPI\n\n'
        'app = FastAPI()\n\n'
        '@app.get("/items")\n'
        'def list_items():\n'
        '    """Retrieve all inventory items."""\n'
        '    return []\n\n'
        '@app.post("/items")\n'
        'def create_item():\n'
        '    """Create a new inventory item."""\n'
        '    return {"status": "created"}\n'
    )
    (proj_dir / "main.py").write_text(api_code, encoding="utf-8")
    return proj_dir


def test_readme_generation(sample_api_project, tmp_path):
    """Verify README synthesis includes tech stack, commands, and architecture diagrams."""
    artifacts = ArtifactManager(root_dir=tmp_path / "artifacts")
    doc_agent = DocumentationAgent(artifact_manager=artifacts)

    res = doc_agent.generate_readme(str(sample_api_project))
    assert res["status"] == "success"
    readme_text = res["readme_text"]

    assert "micro-service" in readme_text
    assert "FastAPI" in readme_text
    assert "mermaid" in readme_text
    assert "Running Tests" in readme_text


def test_api_route_extraction(sample_api_project, tmp_path):
    """Verify route parsing extracts HTTP methods, paths, and docstrings."""
    artifacts = ArtifactManager(root_dir=tmp_path / "artifacts")
    doc_agent = DocumentationAgent(artifact_manager=artifacts)

    res = doc_agent.generate_api_docs(str(sample_api_project))
    assert res["status"] == "success"
    assert res["endpoints_count"] >= 2

    endpoints = res["endpoints"]
    methods = [e["method"] for e in endpoints]
    paths = [e["path"] for e in endpoints]

    assert "GET" in methods
    assert "POST" in methods
    assert "/items" in paths


@pytest.mark.asyncio
async def test_registered_documentation_tools(sample_api_project, tmp_path):
    """Verify registered documentation tools execute and verify cleanly."""
    artifacts = ArtifactManager(root_dir=tmp_path / "artifacts")
    doc_agent = DocumentationAgent(artifact_manager=artifacts)

    readme_tool = DocumentationGenerateReadmeTool(doc_agent=doc_agent)
    api_tool = DocumentationGenerateApiDocsTool(doc_agent=doc_agent)
    arch_tool = DocumentationGenerateArchDocTool(doc_agent=doc_agent)

    p_str = str(sample_api_project)

    # 1. Readme Tool
    r_res = await readme_tool.run(project_path=p_str)
    assert (await readme_tool.verify(r_res))["verified"] is True

    # 2. API Docs Tool
    a_res = await api_tool.run(project_path=p_str)
    assert (await api_tool.verify(a_res))["verified"] is True

    # 3. Architecture Tool
    arch_res = await arch_tool.run(project_path=p_str)
    assert (await arch_tool.verify(arch_res))["verified"] is True
