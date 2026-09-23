"""
Integration tests for SHIVANI Voice Pipeline.
"""

import pytest
import numpy as np
from core.config import Settings
from core.orchestrator.orchestrator import Orchestrator
from core.context.conversational import ConversationalContext
from voice.state import AudioState, AudioStateManager
from voice.wakeword.detector import MockWakeWordDetector
from voice.stt.mock_stt import MockSTTProvider
from voice.tts.mock_tts import MockTTSProvider
from voice.pipeline import VoicePipeline


@pytest.fixture
def voice_pipeline(tmp_path):
    settings = Settings(
        LLM_PROVIDER="mock",
        SECURITY_POLICY="lenient",
        CONFIDENCE_THRESHOLD=0.65,
        AUDIT_LOG_PATH=str(tmp_path / "voice_audit.jsonl")
    )
    orch = Orchestrator(settings=settings)
    audio_state = AudioStateManager()
    wake_detector = MockWakeWordDetector(triggered=True)
    stt = MockSTTProvider(default_text="Shivani, list files")
    tts = MockTTSProvider()
    ctx = ConversationalContext()

    pipeline = VoicePipeline(
        orchestrator=orch,
        settings=settings,
        wake_detector=wake_detector,
        stt_provider=stt,
        tts_provider=tts,
        audio_state=audio_state,
        conversational_context=ctx
    )
    return pipeline


@pytest.mark.asyncio
async def test_voice_pipeline_end_to_end(voice_pipeline):
    audio_sample = np.zeros(16000, dtype=np.float32)

    res = await voice_pipeline.process_spoken_instruction(audio_sample, play_tts_response=True)
    assert res["success"] is True
    assert "list files" in res["transcribed_text"]
    assert res["task"]["status"] == "COMPLETED"
    assert res["response_text"] == "Done."
    assert "Done." in voice_pipeline.tts.spoken_texts
    assert voice_pipeline.state_mgr.current_state == AudioState.IDLE


@pytest.mark.asyncio
async def test_voice_pipeline_speech_interruption(voice_pipeline):
    # User says "Shivani stop"
    voice_pipeline.stt.default_text = "Shivani stop"
    audio_sample = np.zeros(16000, dtype=np.float32)

    res = await voice_pipeline.process_spoken_instruction(audio_sample, play_tts_response=True)
    assert res["success"] is True
    assert "Interrupted" in res["message"]
    assert voice_pipeline.state_mgr.current_state == AudioState.IDLE


@pytest.mark.asyncio
async def test_voice_pipeline_low_confidence_clarification(voice_pipeline):
    # Set low confidence recognition (e.g. 0.40 < 0.65 threshold)
    voice_pipeline.stt.default_text = "Chrome kholo"
    voice_pipeline.stt.confidence = 0.40
    audio_sample = np.zeros(16000, dtype=np.float32)

    res = await voice_pipeline.process_spoken_instruction(audio_sample, play_tts_response=True)
    assert res["requires_clarification"] is True
    assert "क्या आपने कहा कि" in res["question"]
    # Task should not be executed when clarification is required
    assert "task" not in res
    assert voice_pipeline.state_mgr.current_state == AudioState.IDLE
