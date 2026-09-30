"""
SHIVANI pyttsx3 Offline TTS Provider
Offline speech synthesis using Windows SAPI5 / system text-to-speech.
Thread-safe with proper engine lifecycle management.
"""

import time
import asyncio
import threading
from typing import Any, Dict, Optional
from voice.tts.base import TTSProvider, AudioResult


class Pyttsx3TTSProvider(TTSProvider):
    name = "pyttsx3"

    def __init__(self, voice_name: str = "female"):
        self.voice_name = voice_name
        self.rate = 180
        self._is_speaking = False
        self._interrupted = False
        self._lock = threading.Lock()
        self._engine = None

    def _get_engine(self):
        """Get or create the pyttsx3 engine (must be called from same thread)."""
        import pyttsx3
        if self._engine is None:
            self._engine = pyttsx3.init()
        return self._engine

    def set_voice(self, voice_name: str) -> None:
        self.voice_name = voice_name

    def set_rate(self, rate: str) -> None:
        try:
            self.rate = int(rate.replace("%", "").replace("+", "")) + 180
        except Exception:
            pass

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self) -> None:
        self._interrupted = True
        self._is_speaking = False
        with self._lock:
            if self._engine is not None:
                try:
                    self._engine.stop()
                except Exception:
                    pass

    async def speak(self, text: str, play_audio: bool = True) -> AudioResult:
        if not text.strip():
            return AudioResult(text="")

        self._interrupted = False
        start = time.perf_counter()

        def _sync_speak():
            with self._lock:
                import pyttsx3
                # Create a fresh engine per invocation in the worker thread
                # since pyttsx3 engines are not thread-safe across threads
                engine = pyttsx3.init()
                self._engine = engine
                engine.setProperty("rate", self.rate)
                # Find female voice if available
                voices = engine.getProperty("voices")
                for v in voices:
                    if "zira" in v.name.lower() or "female" in v.name.lower():
                        engine.setProperty("voice", v.id)
                        break
                if not self._interrupted:
                    engine.say(text)
                    engine.runAndWait()
                self._engine = None

        if play_audio and not self._interrupted:
            self._is_speaking = True
            try:
                loop = asyncio.get_running_loop()
                await loop.run_in_executor(None, _sync_speak)
            finally:
                self._is_speaking = False

        elapsed = time.perf_counter() - start
        return AudioResult(text=text, duration_seconds=round(elapsed, 2), interrupted=self._interrupted)

    async def health_check(self) -> Dict[str, Any]:
        return {"healthy": True, "provider": "pyttsx3", "voice": self.voice_name}
