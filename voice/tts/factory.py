"""
SHIVANI TTS Factory
Instantiates and configures the active Text-to-Speech provider.
"""

from core.config import Settings
from voice.tts.base import TTSProvider
from voice.tts.mock_tts import MockTTSProvider
from voice.tts.edge_tts_provider import EdgeTTSProvider
from voice.tts.pyttsx3_provider import Pyttsx3TTSProvider


def create_tts_provider(settings: Settings) -> TTSProvider:
    provider = settings.TTS_PROVIDER.lower()

    if provider == "edge_tts":
        try:
            return EdgeTTSProvider(
                voice=settings.TTS_VOICE,
                rate=settings.TTS_RATE,
                output_dir=settings.AUDIO_OUTPUT_DIR
            )
        except Exception as e:
            print(f"[WARN] Failed to load EdgeTTSProvider ({e}). Trying pyttsx3.")
            provider = "pyttsx3"

    if provider == "pyttsx3":
        try:
            return Pyttsx3TTSProvider()
        except Exception as e:
            print(f"[WARN] Failed to load Pyttsx3TTSProvider ({e}). Falling back to MockTTSProvider.")
            return MockTTSProvider()

    return MockTTSProvider()
