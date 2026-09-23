"""
SHIVANI Mock TTS Provider
Deterministic speech synthesis provider for unit testing with interruption verification.
"""

from typing import Any, Dict
from voice.tts.base import TTSProvider, AudioResult


class MockTTSProvider(TTSProvider):
    name = "mock"

    def __init__(self, voice_name: str = "mock_female"):
        self.voice_name = voice_name
        self.rate = "+0%"
        self._is_speaking = False
        self._interrupted = False
        self.spoken_texts = []

    def set_voice(self, voice_name: str) -> None:
        self.voice_name = voice_name

    def set_rate(self, rate: str) -> None:
        self.rate = rate

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self) -> None:
        self._interrupted = True
        self._is_speaking = False

    async def speak(self, text: str, play_audio: bool = True) -> AudioResult:
        self._interrupted = False
        self.spoken_texts.append(text)
        return AudioResult(
            text=text,
            audio_bytes=b"MOCK_PCM_AUDIO",
            duration_seconds=0.02,
            interrupted=self._interrupted
        )

    async def health_check(self) -> Dict[str, Any]:
        return {"healthy": True, "provider": "mock", "status": "operational"}
