"""
SHIVANI pyttsx3 Offline TTS Provider
Offline speech synthesis using Windows SAPI5 / system text-to-speech.
"""

import time
import asyncio
from typing import Any, Dict
from voice.tts.base import TTSProvider, AudioResult


class Pyttsx3TTSProvider(TTSProvider):
    name = "pyttsx3"

    def __init__(self, voice_name: str = "female"):
        self.voice_name = voice_name
        self.rate = 180
        self._is_speaking = False
        self._interrupted = False

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
        try:
            import pyttsx3
            engine = pyttsx3.init()
            engine.stop()
        except Exception:
            pass

    async def speak(self, text: str, play_audio: bool = True) -> AudioResult:
        if not text.strip():
            return AudioResult(text="")

        self._interrupted = False
        start = time.perf_counter()

        def _sync_speak():
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", self.rate)
            # Find female voice if available
            voices = engine.getProperty("voices")
            for v in voices:
                if "zira" in v.name.lower() or "female" in v.name.lower():
                    engine.setProperty("voice", v.id)
                    break
            engine.say(text)
            engine.runAndWait()

        if play_audio and not self._interrupted:
            self._is_speaking = True
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, _sync_speak)
            self._is_speaking = False

        elapsed = time.perf_counter() - start
        return AudioResult(text=text, duration_seconds=round(elapsed, 2), interrupted=self._interrupted)

    async def health_check(self) -> Dict[str, Any]:
        return {"healthy": True, "provider": "pyttsx3", "voice": self.voice_name}
