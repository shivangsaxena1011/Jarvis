"""
Unit tests for SHIVANI Text-to-Speech (TTS) Subsystem & Interruption.
"""

import pytest
from core.config import Settings
from voice.tts.mock_tts import MockTTSProvider
from voice.tts.edge_tts_provider import EdgeTTSProvider
from voice.tts.factory import create_tts_provider


@pytest.mark.asyncio
async def test_mock_tts_lifecycle():
    tts = MockTTSProvider()
    res = await tts.speak("Done. The song is playing.")

    assert res.text == "Done. The song is playing."
    assert "Done. The song is playing." in tts.spoken_texts
    assert res.interrupted is False

    health = await tts.health_check()
    assert health["healthy"] is True


def test_speech_interruption():
    tts = MockTTSProvider()
    tts._is_speaking = True

    # User interrupts: "Shivani stop"
    tts.stop()
    assert tts.is_speaking() is False
    assert tts._interrupted is True


def test_edge_tts_configuration(tmp_path):
    tts = EdgeTTSProvider(voice="hi-IN-SwaraNeural", rate="+10%", output_dir=str(tmp_path))
    assert tts.voice == "hi-IN-SwaraNeural"
    assert tts.rate == "+10%"

    tts.set_voice("en-IN-NeerjaNeural")
    assert tts.voice == "en-IN-NeerjaNeural"

    tts.set_rate("-5%")
    assert tts.rate == "-5%"


def test_tts_factory():
    settings_mock = Settings(TTS_PROVIDER="mock")
    tts_mock = create_tts_provider(settings_mock)
    assert isinstance(tts_mock, MockTTSProvider)

    settings_edge = Settings(TTS_PROVIDER="edge_tts")
    tts_edge = create_tts_provider(settings_edge)
    assert isinstance(tts_edge, (EdgeTTSProvider, MockTTSProvider))
