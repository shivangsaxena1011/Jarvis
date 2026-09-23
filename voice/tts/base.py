"""
SHIVANI Text-to-Speech (TTS) Base Interface
Provides speech synthesis, natural voice selection, and immediate speech interruption.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pydantic import BaseModel


class AudioResult(BaseModel):
    text: str
    audio_path: Optional[str] = None
    audio_bytes: Optional[bytes] = None
    duration_seconds: float = 0.0
    interrupted: bool = False


class TTSProvider(ABC):
    """Abstract interface for Text-to-Speech providers."""

    name: str = "base"

    @abstractmethod
    async def speak(self, text: str, play_audio: bool = True) -> AudioResult:
        """Synthesizes text into speech and optionally plays through system speaker."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Immediately halts active audio speech playback (interruption)."""
        pass

    @abstractmethod
    def set_voice(self, voice_name: str) -> None:
        """Configures the target voice identity."""
        pass

    @abstractmethod
    def set_rate(self, rate: str) -> None:
        """Configures speech rate (e.g. '+0%', '+10%')."""
        pass

    @abstractmethod
    def is_speaking(self) -> bool:
        """Returns True if speech audio is currently playing."""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Validates TTS engine availability."""
        pass
