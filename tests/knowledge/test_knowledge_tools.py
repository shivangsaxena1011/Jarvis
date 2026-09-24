"""
Unit Tests for Knowledge OS Tools
"""

from pathlib import Path
import pytest
from knowledge.service import KnowledgeOS
from tools.knowledge_tools import (
    KnowledgeAddNoteTool,
    KnowledgeGetProjectContextTool,
    KnowledgeIndexPathTool,
    KnowledgeQueryGraphTool,
    KnowledgeSearchTool,
)


@pytest.fixture
def knowledge_tools(tmp_path):
    db_file = tmp_path / "tools_test.db"
    kos = KnowledgeOS(db_path=str(db_file))
    yield kos
    kos.close()


@pytest.mark.asyncio
async def test_knowledge_tools_execution(knowledge_tools, tmp_path):
    kos = knowledge_tools

    # 1. Add Note Tool
    add_note_tool = KnowledgeAddNoteTool(knowledge_os=kos)
    note_res = await add_note_tool.run(
        title="Testing Note",
        content="Testing note tool functionality in automated suite.",
        is_decision=False,
    )
    assert note_res["success"] is True

    # 2. Search Tool
    search_tool = KnowledgeSearchTool(knowledge_os=kos)
    search_res = await search_tool.run(query="Testing note tool")
    assert "Testing note tool" in search_res["context"]

    # 3. Index Path Tool
    test_doc = tmp_path / "PRD.md"
    test_doc.write_text("# Product Specs\nRequirements for high-speed indexing.", encoding="utf-8")
    index_tool = KnowledgeIndexPathTool(knowledge_os=kos)
    index_res = await index_tool.run(path=str(test_doc))
    assert index_res["success"] is True

    # 4. Project Context Tool
    proj_tool = KnowledgeGetProjectContextTool(knowledge_os=kos)
    proj_res = await proj_tool.run(project_id_or_path=str(tmp_path))
    assert "project_context" in proj_res
    assert "# Project:" in proj_res["project_context"]

    # 5. Query Graph Tool
    graph_tool = KnowledgeQueryGraphTool(knowledge_os=kos)
    graph_res = await graph_tool.run(start_node="test_node", max_depth=1)
    assert graph_res["start_node"] == "test_node"
