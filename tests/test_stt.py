"""
Unit tests for SHIVANI Speech-to-Text (STT) Subsystem.
"""

import pytest
import numpy as np
from core.config import Settings
from voice.stt.mock_stt import MockSTTProvider
from voice.stt.whisper_stt import FasterWhisperSTT
from voice.stt.factory import create_stt_provider


@pytest.mark.asyncio
async def test_mock_stt_provider():
    stt = MockSTTProvider(default_text="Shivani, screenshot capture karo")
    audio = np.zeros(16000, dtype=np.float32)

    res = await stt.transcribe(audio, language="hi")
    assert res.text == "Shivani, screenshot capture karo"
    assert res.language == "hi"
    assert res.confidence >= 0.9
    assert len(res.segments) == 1

    health = await stt.health_check()
    assert health["healthy"] is True


def test_stt_factory():
    settings_mock = Settings(STT_PROVIDER="mock")
    provider = create_stt_provider(settings_mock)
    assert isinstance(provider, MockSTTProvider)

    settings_whisper = Settings(STT_PROVIDER="whisper", STT_MODEL="tiny")
    provider_whisper = create_stt_provider(settings_whisper)
    assert isinstance(provider_whisper, FasterWhisperSTT)
