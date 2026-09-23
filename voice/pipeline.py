"""
SHIVANI Voice Pipeline
Coordinates Audio State, Local Wake Word, STT, Conversational Context,
Task Execution, and TTS with immediate speech interruption.
"""

import time
import asyncio
from typing import Any, Dict, Optional, Union
import numpy as np

from core.config import Settings, get_settings
from core.orchestrator.orchestrator import Orchestrator
from core.tasks.task import Task, TaskStatus
from core.context.conversational import ConversationalContext, get_conversational_context
from voice.state import AudioState, AudioStateManager, get_audio_state_manager
from voice.wakeword.detector import WakeWordDetector, LocalWakeWordDetector
from voice.stt.base import STTProvider, TranscriptionResult
from voice.stt.factory import create_stt_provider
from voice.tts.base import TTSProvider, AudioResult
from voice.tts.factory import create_tts_provider


class VoicePipeline:
    def __init__(
        self,
        orchestrator: Orchestrator,
        settings: Optional[Settings] = None,
        wake_detector: Optional[WakeWordDetector] = None,
        stt_provider: Optional[STTProvider] = None,
        tts_provider: Optional[TTSProvider] = None,
        audio_state: Optional[AudioStateManager] = None,
        conversational_context: Optional[ConversationalContext] = None
    ):
        self.orchestrator = orchestrator
        self.settings = settings or get_settings()
        self.state_mgr = audio_state or get_audio_state_manager()
        self.wake_detector = wake_detector or LocalWakeWordDetector()
        self.stt = stt_provider or create_stt_provider(self.settings)
        self.tts = tts_provider or create_tts_provider(self.settings)
        self.context = conversational_context or get_conversational_context()

    def interrupt(self) -> None:
        """Immediately halts active speech and aborts running tasks."""
        self.tts.stop()
        self.orchestrator.stop_all()
        self.state_mgr.transition_to(AudioState.IDLE, {"interrupted": True})

    async def process_spoken_instruction(
        self,
        audio_data: Union[np.ndarray, bytes],
        sample_rate: int = 16000,
        play_tts_response: bool = True
    ) -> Dict[str, Any]:
        """
        Full pipeline: Audio In -> STT -> Context -> Orchestrator -> TTS -> Audio Out.
        """
        # 1. State: PROCESSING
        self.state_mgr.transition_to(AudioState.PROCESSING)

        try:
            # 2. Transcribe Audio
            tr: TranscriptionResult = await self.stt.transcribe(audio_data, sample_rate=sample_rate)
            raw_text = tr.text.strip()

            if not raw_text:
                self.state_mgr.transition_to(AudioState.IDLE)
                return {
                    "success": False,
                    "text": "",
                    "message": "No speech detected in audio."
                }

            # Check for Interruption command ("Shivani stop")
            if "stop" in raw_text.lower():
                self.interrupt()
                return {
                    "success": True,
                    "text": raw_text,
                    "message": "Interrupted by user."
                }

            # Strip wake word if present
            stripped = self.wake_detector.strip_wake_word(raw_text) if hasattr(self.wake_detector, "strip_wake_word") else raw_text
            effective_query = stripped or raw_text

            # 3. Check for Low Confidence Uncertainty
            clarification = self.context.check_uncertainty_clarification(
                effective_query,
                confidence=tr.confidence,
                threshold=self.settings.CONFIDENCE_THRESHOLD
            )
            if clarification:
                self.state_mgr.transition_to(AudioState.SPEAKING)
                tts_res = await self.tts.speak(clarification, play_audio=play_tts_response)
                self.state_mgr.transition_to(AudioState.IDLE)
                return {
                    "success": False,
                    "requires_clarification": True,
                    "question": clarification,
                    "transcribed": raw_text,
                    "confidence": tr.confidence,
                    "tts": tts_res.model_dump()
                }

            # 4. Multi-turn Conversational Context resolution
            resolved_query = self.context.resolve_followup(effective_query)
            self.context.record_turn(role="user", text=resolved_query, confidence=tr.confidence)

            # Optional brief acknowledgment for conversational feel ("Sure")
            if play_tts_response and not self.tts.is_speaking():
                asyncio.create_task(self.tts.speak("Sure.", play_audio=True))

            # 5. Submit to Orchestrator
            task: Task = await self.orchestrator.submit_task(resolved_query)

            # Await task execution completion
            while task.status in (
                TaskStatus.PENDING,
                TaskStatus.PLANNING,
                TaskStatus.WAITING_FOR_PERMISSION,
                TaskStatus.EXECUTING,
                TaskStatus.VERIFYING
            ):
                await asyncio.sleep(0.1)

            # 6. Formulate Concise Response
            if task.status == TaskStatus.COMPLETED:
                response_text = "Done."
            elif task.status == TaskStatus.CANCELLED:
                response_text = "Cancelled."
            else:
                response_text = f"I could not complete that: {task.error or 'Failed'}"

            self.context.record_turn(role="shivani", text=response_text, task_id=task.id)

            # 7. Speak Response (TTS)
            self.state_mgr.transition_to(AudioState.SPEAKING)
            tts_res = await self.tts.speak(response_text, play_audio=play_tts_response)
            self.state_mgr.transition_to(AudioState.IDLE)

            return {
                "success": task.status == TaskStatus.COMPLETED,
                "transcribed_text": raw_text,
                "resolved_query": resolved_query,
                "language": tr.language,
                "confidence": tr.confidence,
                "task": task.model_dump(),
                "response_text": response_text,
                "tts": tts_res.model_dump()
            }

        except Exception as e:
            self.state_mgr.transition_to(AudioState.ERROR, {"error": str(e)})
            raise e
