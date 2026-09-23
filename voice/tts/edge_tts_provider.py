"""
SHIVANI Edge-TTS Provider
High-quality neural female voice synthesis using Microsoft Edge TTS.
Supports Hindi (hi-IN-SwaraNeural), Indian English (en-IN-NeerjaNeural), and US English.
Implements instant audio playback cancellation (<50ms).
"""

import os
import time
import uuid
import asyncio
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from voice.tts.base import TTSProvider, AudioResult
from core.errors import ProviderError


class EdgeTTSProvider(TTSProvider):
    name = "edge_tts"

    def __init__(
        self,
        voice: str = "hi-IN-SwaraNeural",
        rate: str = "+0%",
        output_dir: str = "audio_cache"
    ):
        self.voice = voice
        self.rate = rate
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._active_proc: Optional[subprocess.Popen] = None
        self._is_speaking = False
        self._interrupted = False

    def set_voice(self, voice_name: str) -> None:
        self.voice = voice_name

    def set_rate(self, rate: str) -> None:
        self.rate = rate

    def is_speaking(self) -> bool:
        return self._is_speaking

    def stop(self) -> None:
        """Immediately halts any playing audio subprocess."""
        self._interrupted = True
        if self._active_proc:
            try:
                self._active_proc.terminate()
                self._active_proc.kill()
            except Exception:
                pass
            self._active_proc = None
        self._is_speaking = False

    async def speak(self, text: str, play_audio: bool = True) -> AudioResult:
        if not text.strip():
            return AudioResult(text="")

        self._interrupted = False
        file_id = f"speech_{uuid.uuid4().hex[:8]}.mp3"
        dest_path = self.output_dir / file_id
        start_time = time.perf_counter()

        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
            await communicate.save(str(dest_path))

            with open(dest_path, "rb") as f:
                audio_bytes = f.read()

            elapsed = time.perf_counter() - start_time

            # Play audio if requested and not interrupted
            if play_audio and not self._interrupted:
                self._is_speaking = True
                await self._play_audio_file(dest_path)
                self._is_speaking = False

            return AudioResult(
                text=text,
                audio_path=str(dest_path.resolve()),
                audio_bytes=audio_bytes,
                duration_seconds=round(elapsed, 2),
                interrupted=self._interrupted
            )
        except Exception as e:
            self._is_speaking = False
            raise ProviderError(f"Edge TTS synthesis failed: {e}")

    async def _play_audio_file(self, file_path: Path) -> None:
        """Plays audio in an interruptible background process."""
        # Use Windows Media Player command line or PowerShell SoundPlayer for interruptible audio
        cmd = [
            "powershell",
            "-NoProfile",
            "-Command",
            f"""
            Add-Type -AssemblyName presentationCore
            $player = New-Object System.Windows.Media.MediaPlayer
            $player.Open([System.Uri]'{str(file_path.resolve())}')
            $player.Play()
            while ($player.NaturalDuration.HasTimeSpan -eq $false) {{ Start-Sleep -Milliseconds 50 }}
            Start-Sleep -Seconds ($player.NaturalDuration.TimeSpan.TotalSeconds)
            $player.Close()
            """
        ]

        try:
            self._active_proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            # Await completion while checking for interruption
            while self._active_proc.poll() is None:
                if self._interrupted:
                    self.stop()
                    break
                await asyncio.sleep(0.05)
        except Exception:
            pass
        finally:
            self._active_proc = None

    async def health_check(self) -> Dict[str, Any]:
        try:
            import edge_tts
            return {
                "healthy": True,
                "provider": "edge_tts",
                "voice": self.voice,
                "rate": self.rate
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": "edge_tts",
                "error": str(e)
            }
