"""
SHIVANI Presentation Agent Data Models
Structured data contracts for presentation decks, slide definitions, speaker notes,
multi-duration pitches, and judge Q&A preparation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class PresentationMode(str, Enum):
    HACKATHON = "hackathon"
    TECHNICAL = "technical"
    EXECUTIVE = "executive"


class SlideDefinition(BaseModel):
    """Specification of a single slide in a deck."""
    slide_number: int
    title: str
    subtitle: Optional[str] = None
    category: str = "content"  # title, problem, solution, architecture, features, demo, impact, conclusion
    bullet_points: List[str] = Field(default_factory=list)
    callout: Optional[str] = None
    speaker_notes: str = ""
    visual_layout: str = "standard"  # title_slide, two_column, metric_grid, card_layout


class PresentationDeck(BaseModel):
    """Complete presentation bundle containing metadata, slides, and paths."""
    title: str
    subtitle: str = ""
    mode: PresentationMode
    target_duration_minutes: int = 5
    slides: List[SlideDefinition] = Field(default_factory=list)
    pptx_path: Optional[str] = None
    total_slides: int = 0
    pitch_bundle: Optional[Dict[str, str]] = None
    qa_bundle: List[Dict[str, str]] = Field(default_factory=list)
    review_issues: List[str] = Field(default_factory=list)


class PitchBundle(BaseModel):
    """Multi-duration pitch scripts tailored for hackathons and demo days."""
    pitch_30s: str
    pitch_1m: str
    pitch_3m: str
    pitch_5m: str


class QAItem(BaseModel):
    """Expected question, suggested answer, and supporting evidence."""
    category: str  # Technical, Business, Security, Scalability, AI/ML, Data, Deployment, Innovation
    question: str
    suggested_answer: str
    evidence: str
