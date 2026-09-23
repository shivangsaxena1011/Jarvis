"""
SHIVANI Wake Word Detector
Local wake word detection for 'Shivani'. Processes audio locally without continuous remote upload.
"""

from abc import ABC, abstractmethod
import re
from typing import Any, Dict, Optional
import numpy as np


class WakeWordDetector(ABC):
    """Abstract interface for wake word detection engines."""

    @abstractmethod
    def detect_in_audio(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """Processes raw audio buffer and returns True if 'Shivani' wake word is detected."""
        pass

    @abstractmethod
    def detect_in_text(self, text: str) -> bool:
        """Determines if wake word is present in a transcript snippet."""
        pass


class LocalWakeWordDetector(WakeWordDetector):
    """
    Local privacy-first wake word detector.
    Uses acoustic energy thresholding and fuzzy phonetic matching for 'Shivani'.
    """

    WAKE_PATTERNS = [
        r"\bshivani\b",
        r"\bshiwani\b",
        r"\bshivanee\b",
        r"\bshivaani\b",
        r"\bshibani\b",
        r"\bshivan\b",
        r"\bhey\s+shivani\b",
        r"\bsuno\s+shivani\b",
    ]

    def __init__(self, energy_threshold: float = 0.015):
        self.energy_threshold = energy_threshold

    def calculate_energy(self, audio_chunk: np.ndarray) -> float:
        """Calculates RMS energy of an audio buffer."""
        if len(audio_chunk) == 0:
            return 0.0
        float_chunk = audio_chunk.astype(np.float32)
        if np.max(np.abs(float_chunk)) > 1.0:
            float_chunk = float_chunk / 32768.0
        return float(np.sqrt(np.mean(float_chunk ** 2)))

    def detect_in_audio(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        Local energy check to filter out ambient silence before deeper processing.
        """
        energy = self.calculate_energy(audio_chunk)
        return energy > self.energy_threshold

    def detect_in_text(self, text: str) -> bool:
        """
        Checks whether wake word 'Shivani' or common phonetic transcription variants occur in text.
        """
        clean = text.lower().strip()
        for pat in self.WAKE_PATTERNS:
            if re.search(pat, clean):
                return True
        return False

    def strip_wake_word(self, text: str) -> str:
        """Removes the wake word prefix from query."""
        clean = text.strip()
        for pat in self.WAKE_PATTERNS:
            clean = re.sub(rf"^{pat}[,\s]*", "", clean, flags=re.IGNORECASE)
        return clean.strip()


class MockWakeWordDetector(WakeWordDetector):
    """Mock detector for deterministic testing."""

    def __init__(self, triggered: bool = False):
        self.triggered = triggered

    def detect_in_audio(self, audio_chunk: np.ndarray, sample_rate: int = 16000) -> bool:
        return self.triggered

    def detect_in_text(self, text: str) -> bool:
        return "shivani" in text.lower()
