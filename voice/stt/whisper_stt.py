"""
SHIVANI Faster-Whisper Local STT Provider
Provides low-latency local transcription using faster-whisper on CPU/GPU.
Supports English, Hindi, and mixed Hinglish speech.
"""

import io
import time
import tempfile
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional, Union
import numpy as np

from voice.stt.base import STTProvider, TranscriptionResult
from core.errors import ProviderError


class FasterWhisperSTT(STTProvider):
    name = "whisper"

    def __init__(self, model_size: str = "tiny", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._lock = asyncio.Lock()

    def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type
            )
        return self._model

    async def transcribe(
        self,
        audio_data: Union[np.ndarray, bytes],
        sample_rate: int = 16000,
        language: Optional[str] = None
    ) -> TranscriptionResult:
        start_time = time.perf_counter()

        def _run_transcription():
            model = self._get_model()
            
            # Prepare audio target
            if isinstance(audio_data, bytes):
                # Save bytes to a temporary wav/audio file for robust container decoding
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                    tmp.write(audio_data)
                    tmp_path = tmp.name

                try:
                    segments, info = model.transcribe(
                        tmp_path,
                        beam_size=2,
                        language=language,
                        vad_filter=True
                    )
                    seg_list = list(segments)
                finally:
                    try:
                        Path(tmp_path).unlink(missing_ok=True)
                    except Exception:
                        pass
            else:
                # Numpy array
                arr = audio_data.astype(np.float32)
                if np.max(np.abs(arr)) > 1.0:
                    arr = arr / 32768.0

                segments, info = model.transcribe(
                    arr,
                    beam_size=2,
                    language=language,
                    vad_filter=True
                )
                seg_list = list(segments)

            text = " ".join([s.text for s in seg_list]).strip()
            # Calculate average probability as confidence
            conf = 1.0
            if seg_list:
                conf = float(np.mean([np.exp(s.avg_logprob) for s in seg_list]))

            return text, info.language, conf, [
                {"id": s.id, "text": s.text, "start": s.start, "end": s.end} for s in seg_list
            ]

        try:
            loop = asyncio.get_running_loop()
            async with self._lock:
                text, lang, conf, segs = await loop.run_in_executor(None, _run_transcription)
            
            elapsed = time.perf_counter() - start_time
            return TranscriptionResult(
                text=text,
                language=lang,
                confidence=round(conf, 2),
                duration_seconds=round(elapsed, 3),
                segments=segs
            )
        except Exception as e:
            raise ProviderError(f"Whisper transcription failed: {e}")

    async def health_check(self) -> Dict[str, Any]:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._get_model)
            return {
                "healthy": True,
                "provider": "whisper",
                "model_size": self.model_size,
                "device": self.device
            }
        except Exception as e:
            return {
                "healthy": False,
                "provider": "whisper",
                "error": str(e)
            }
