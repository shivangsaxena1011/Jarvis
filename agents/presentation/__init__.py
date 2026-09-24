"""
SHIVANI Presentation Agent Package
"""

from agents.presentation.agent import PresentationAgent
from agents.presentation.models import (
    PresentationMode,
    SlideDefinition,
    PresentationDeck,
    PitchBundle,
    QAItem,
)

__all__ = [
    "PresentationAgent",
    "PresentationMode",
    "SlideDefinition",
    "PresentationDeck",
    "PitchBundle",
    "QAItem",
]
