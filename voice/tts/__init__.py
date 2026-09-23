"""SHIVANI TTS Package"""
from voice.tts.base import TTSProvider, AudioResult
from voice.tts.mock_tts import MockTTSProvider
from voice.tts.edge_tts_provider import EdgeTTSProvider
from voice.tts.pyttsx3_provider import Pyttsx3TTSProvider
from voice.tts.factory import create_tts_provider

__all__ = [
    "TTSProvider",
    "AudioResult",
    "MockTTSProvider",
    "EdgeTTSProvider",
    "Pyttsx3TTSProvider",
    "create_tts_provider",
]
