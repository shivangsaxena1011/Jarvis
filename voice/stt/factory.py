"""
SHIVANI STT Factory
Instantiates the configured Speech-to-Text provider.
"""

from core.config import Settings
from voice.stt.base import STTProvider
from voice.stt.mock_stt import MockSTTProvider
from voice.stt.whisper_stt import FasterWhisperSTT


def create_stt_provider(settings: Settings) -> STTProvider:
    provider = settings.STT_PROVIDER.lower()

    if provider in ("whisper", "local", "faster-whisper"):
        try:
            return FasterWhisperSTT(model_size=settings.STT_MODEL)
        except Exception as e:
            print(f"[WARN] Failed to load Whisper STT ({e}). Falling back to MockSTTProvider.")
            return MockSTTProvider()

    return MockSTTProvider()
