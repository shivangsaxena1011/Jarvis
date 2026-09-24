"""
Unit Tests for Agent Integrations with Knowledge OS
"""

from pathlib import Path
import pytest
from agents.coding.agent import CodingAgent
from agents.presentation.agent import PresentationAgent
from agents.research.agent import ResearchAgent
from knowledge.models import KnowledgeType
from knowledge.service import KnowledgeOS


@pytest.fixture
def agent_kos(tmp_path):
    db_file = tmp_path / "agents_test.db"
    kos = KnowledgeOS(db_path=str(db_file))
    yield kos
    kos.close()


def test_coding_agent_knowledge_integration(agent_kos, tmp_path):
    # Seed knowledge base with architectural decision
    agent_kos.add_note(
        title="Coding Architecture",
        content="All endpoints must use async def and return typed Pydantic models.",
        is_decision=True,
    )

    coding_agent = CodingAgent(knowledge_os=agent_kos)
    k_res = coding_agent.query_codebase_knowledge("endpoints Pydantic models")
    assert "async def and return typed Pydantic models" in k_res["context"]


@pytest.mark.asyncio
async def test_research_agent_knowledge_integration(agent_kos):
    research_agent = ResearchAgent(knowledge_os=agent_kos)
    bundle = await research_agent.conduct_research(topic="Distributed Consensus Algorithms", max_sources=2)
    assert bundle is not None

    # Verify that research findings were indexed into Knowledge OS
    items = agent_kos.store.list_items(type=KnowledgeType.RESEARCH_SOURCE)
    assert len(items) >= 1
    assert "Distributed Consensus" in items[0].title


def test_presentation_agent_knowledge_integration(agent_kos, tmp_path):
    # Create mock project
    proj_dir = tmp_path / "my_app"
    proj_dir.mkdir()
    (proj_dir / "pyproject.toml").write_text('[project]\nname = "my_app"\nversion = "1.0.0"\n', encoding="utf-8")
    (proj_dir / "README.md").write_text("# My App\nCutting edge knowledge platform.", encoding="utf-8")

    pres_agent = PresentationAgent(knowledge_os=agent_kos)
    deck = pres_agent.build_deck_from_project(str(proj_dir))
    assert deck is not None
    assert "my_app" in deck.title or "My App" in deck.title
    assert len(deck.slides) >= 5
