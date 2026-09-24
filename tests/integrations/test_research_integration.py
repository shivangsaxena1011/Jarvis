"""
Unit & Integration Tests for SHIVANI Research Integration & Tools.
Verifies multi-source search, provenance tracking, and reporting artifacts.
"""

import pytest
from pathlib import Path
from integrations.research.service import ResearchService
from tools.integrations.research_tools import (
    ResearchSearchTool,
    ResearchOpenSourceTool,
    ResearchSummarizeTool,
    ResearchSaveReportTool,
)


@pytest.mark.asyncio
async def test_research_search_and_provenance():
    """Verify research search extracts sources with title, URL, publisher, date, and relevance."""
    service = ResearchService()
    res = await service.search(query="Multi-Agent Systems", limit=4)
    
    assert res["status"] == "success"
    assert res["count"] > 0
    sources = res["sources"]
    assert len(sources) <= 4
    
    for s in sources:
        assert "id" in s
        assert "title" in s
        assert "url" in s
        assert "publisher" in s
        assert "date" in s
        assert "relevance" in s


@pytest.mark.asyncio
async def test_research_report_generation(tmp_path):
    """Verify report bundling creates report.md, sources.json, and summary.json on disk."""
    out_dir = tmp_path / "research_test_output"
    service = ResearchService(output_dir=str(out_dir))
    
    topic = "Autonomous Computer Control"
    search_res = await service.search(query=topic, limit=3)
    sources = search_res["sources"]
    
    summary = service.summarize_sources(query=topic, sources=sources)
    assert len(summary) > 50
    assert "Takeaways" in summary or "Synthesis" in summary
    
    saved = await service.save_report(query=topic, summary=summary, sources=sources, output_dir=str(out_dir))
    assert saved["status"] == "saved"
    
    rep_md = Path(saved["report_path"])
    src_json = Path(saved["sources_path"])
    sum_json = Path(saved["summary_path"])
    
    assert rep_md.exists() and rep_md.stat().st_size > 0
    assert src_json.exists() and src_json.stat().st_size > 0
    assert sum_json.exists() and sum_json.stat().st_size > 0
    
    # Check markdown has cited sources table
    content = rep_md.read_text(encoding="utf-8")
    assert "## Cited Sources" in content
    assert "| Title |" in content


@pytest.mark.asyncio
async def test_research_registered_tools(tmp_path):
    """Verify all registered Research tools execute and verify cleanly."""
    out_dir = tmp_path / "research_tools_out"
    service = ResearchService(output_dir=str(out_dir))
    
    search_tool = ResearchSearchTool(research_service=service)
    source_tool = ResearchOpenSourceTool(research_service=service)
    sum_tool = ResearchSummarizeTool(research_service=service)
    save_tool = ResearchSaveReportTool(research_service=service)
    
    # 1. Search tool
    s_res = await search_tool.run(query="Neural Networks", limit=3)
    assert (await search_tool.verify(s_res))["verified"] is True
    
    # 2. Source tool
    o_res = await source_tool.run(url="https://arxiv.org/abs/2301.00001")
    assert (await source_tool.verify(o_res))["verified"] is True
    
    # 3. Summarize tool
    sm_res = await sum_tool.run(query="Neural Networks")
    assert (await sum_tool.verify(sm_res))["verified"] is True
    
    # 4. Save report tool
    sv_res = await save_tool.run(query="Neural Networks", output_dir=str(out_dir))
    assert (await save_tool.verify(sv_res))["verified"] is True
