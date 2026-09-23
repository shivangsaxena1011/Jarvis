"""
SHIVANI Mock STT Provider
Deterministic speech-to-text provider for fast automated tests.
"""

from typing import Any, Dict, Optional, Union
import numpy as np
from voice.stt.base import STTProvider, TranscriptionResult


class MockSTTProvider(STTProvider):
    name = "mock"

    def __init__(self, default_text: str = "Shivani, open notepad"):
        self.default_text = default_text
        self.confidence = 0.98

    async def transcribe(
        self,
        audio_data: Union[np.ndarray, bytes],
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        return TranscriptionResult(
            text=self.default_text,
            language=language or "en",
            confidence=self.confidence,
            duration_seconds=0.01,
            segments=[{"id": 0, "text": self.default_text, "start": 0.0, "end": 1.0}]
        )

    async def health_check(self) -> Dict[str, Any]:
        return {
            "healthy": True,
            "provider": "mock",
            "status": "operational"
        }
