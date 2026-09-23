"""
SHIVANI Speech-to-Text (STT) Base Interface
Defines contracts for transcribing spoken English, Hindi, and Hinglish.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
import numpy as np
from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    text: str
    language: str = "en"
    confidence: float = 1.0
    duration_seconds: float = 0.0
    segments: list[Dict[str, Any]] = Field(default_factory=list)


class STTProvider(ABC):
    """Abstract interface for Speech-to-Text engines."""

    name: str = "base"

    @abstractmethod
    async def transcribe(
        self,
        audio_data: Union[np.ndarray, bytes],
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        """Transcribes raw PCM audio or encoded bytes into text."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Validates STT engine availability."""
        pass
