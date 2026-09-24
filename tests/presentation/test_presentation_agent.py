"""
Unit & Integration Tests for SHIVANI Presentation Agent.
Tests PowerPoint (.pptx) deck generation, slide quality inspection,
multi-duration pitches, judge Q&A preparation, and registered presentation tools.
"""

import pytest
from pathlib import Path
from agents.presentation.agent import PresentationAgent
from agents.presentation.models import PresentationMode
from core.artifacts.manager import ArtifactManager
from tools.presentation import (
    PresentationGenerateDeckTool,
    PresentationGeneratePitchTool,
    PresentationGenerateQATool,
)


@pytest.fixture
def temp_artifact_manager(tmp_path):
    return ArtifactManager(root_dir=tmp_path / "artifacts")


def test_presentation_pptx_deck_generation(temp_artifact_manager):
    """Verify PowerPoint deck generation creates valid .pptx with speaker notes."""
    agent = PresentationAgent(artifact_manager=temp_artifact_manager)

    deck = agent.build_deck(
        title="Shivani Autonomous Operating System",
        project_name="SHIVANI",
        problem_statement="Fragmented AI systems lack autonomous computer-use and safety controls.",
        solution_summary="A voice-first autonomous agent operating Windows and browser with 100% verification.",
        tech_stack=["Python", "FastAPI", "Playwright", "edge-tts"],
        key_features=["Voice control", "Observe-Plan-Act-Verify", "Stage Checkpoints", "Permission Sandboxing"],
        mode=PresentationMode.HACKATHON,
        target_duration=5
    )

    assert deck.total_slides == 7
    assert deck.pptx_path is not None
    assert Path(deck.pptx_path).exists()
    assert Path(deck.pptx_path).stat().st_size > 1000  # Non-empty PPTX

    # Check first slide properties
    first_slide = deck.slides[0]
    assert "Shivani" in first_slide.title
    assert len(first_slide.speaker_notes) > 10

    # Review sanity check
    assert len(deck.review_issues) == 0


def test_presentation_pitches_and_qa(temp_artifact_manager):
    """Verify pitch scripts and 8-category judge Q&A generation."""
    agent = PresentationAgent(artifact_manager=temp_artifact_manager)

    # Pitches
    pitches = agent.generate_pitches(
        project_name="DocVerify AI",
        problem="Manual document fraud checking is slow.",
        solution="Autonomous multimodal document verification.",
        features=["99% Fraud detection", "Sub-second verification"]
    )
    assert len(pitches.pitch_30s) > 50
    assert len(pitches.pitch_1m) > 100
    assert len(pitches.pitch_3m) > 200
    assert len(pitches.pitch_5m) > 300

    # Q&A
    qa_list = agent.generate_qa(
        project_name="DocVerify AI",
        tech_stack=["Python", "FastAPI", "Vision Models"],
        solution="Autonomous document verification"
    )
    categories = {q.category for q in qa_list}
    assert "Technical" in categories
    assert "Security" in categories
    assert "Scalability" in categories
    assert "AI/ML" in categories


@pytest.mark.asyncio
async def test_registered_presentation_tools(temp_artifact_manager):
    """Verify registered presentation tools execute and verify cleanly."""
    agent = PresentationAgent(artifact_manager=temp_artifact_manager)

    deck_tool = PresentationGenerateDeckTool(presentation_agent=agent)
    pitch_tool = PresentationGeneratePitchTool(presentation_agent=agent)
    qa_tool = PresentationGenerateQATool(presentation_agent=agent)

    # 1. Deck Tool
    d_res = await deck_tool.run(
        title="Agentic Future",
        project_name="AgentX",
        problem_statement="AI cannot use computers natively.",
        solution_summary="Autonomous computer agent."
    )
    assert (await deck_tool.verify(d_res))["verified"] is True
    assert d_res["total_slides"] > 0

    # 2. Pitch Tool
    p_res = await pitch_tool.run(
        project_name="AgentX",
        problem="AI friction",
        solution="Autonomous agents"
    )
    assert (await pitch_tool.verify(p_res))["verified"] is True

    # 3. QA Tool
    q_res = await qa_tool.run(
        project_name="AgentX",
        tech_stack=["Python"],
        solution="Autonomous agent"
    )
    assert (await qa_tool.verify(q_res))["verified"] is True
