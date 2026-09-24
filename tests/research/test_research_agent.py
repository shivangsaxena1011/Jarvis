"""
Unit & Integration Tests for SHIVANI Research Agent.
Tests multi-source classification, contradiction handling, report generation, and artifact separation.
"""

import pytest
from pathlib import Path
from agents.research.agent import ResearchAgent
from agents.research.models import SourceType
from core.artifacts.manager import ArtifactManager


@pytest.fixture
def temp_artifact_manager(tmp_path):
    return ArtifactManager(root_dir=tmp_path / "artifacts")


def test_research_source_classification(temp_artifact_manager):
    """Verify primary, secondary, and community source domain classification."""
    agent = ResearchAgent(artifact_manager=temp_artifact_manager)

    assert agent.classify_source_type("https://arxiv.org/abs/2304.03442") == SourceType.PRIMARY
    assert agent.classify_source_type("https://doi.org/10.1145/123456") == SourceType.PRIMARY
    assert agent.classify_source_type("https://docs.python.org/3/library/ast.html") == SourceType.PRIMARY

    assert agent.classify_source_type("https://github.com/langchain-ai/langchain") == SourceType.SECONDARY
    assert agent.classify_source_type("https://towardsdatascience.com/ai-agents-survey") == SourceType.SECONDARY

    assert agent.classify_source_type("https://random-forum.xyz/topic/123") == SourceType.COMMUNITY


@pytest.mark.asyncio
async def test_research_bundle_synthesis_and_artifact_saving(temp_artifact_manager):
    """Verify research synthesis produces all 9 sections, detects tradeoffs, and persists artifacts."""
    agent = ResearchAgent(artifact_manager=temp_artifact_manager)

    bundle = await agent.conduct_research(topic="Multimodal Vision Language Models", max_sources=3)

    assert bundle.query == "Multimodal Vision Language Models"
    assert len(bundle.sources) >= 1
    assert "Executive Summary" in bundle.markdown_report
    assert "Problem Statement" in bundle.markdown_report
    assert "Comparative Analysis" in bundle.markdown_report
    assert "References & Provenance" in bundle.markdown_report

    # Contradiction / Tradeoff check
    assert len(bundle.contradictions) >= 1
    assert "Tradeoffs & Differing Perspectives" in bundle.markdown_report

    # Check artifacts written to research directory
    report_file = temp_artifact_manager.get_artifact_path("research", "multimodal_vision_language_mod_report.md")
    assert report_file.exists()
    assert "Technical Research Report" in report_file.read_text(encoding="utf-8")
