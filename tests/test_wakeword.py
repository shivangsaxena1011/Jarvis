"""
Unit tests for SHIVANI Wake Word Detector.
"""

import numpy as np
from voice.wakeword.detector import LocalWakeWordDetector, MockWakeWordDetector


def test_wake_word_text_detection():
    detector = LocalWakeWordDetector()

    assert detector.detect_in_text("Shivani, open notepad") is True
    assert detector.detect_in_text("Hey shivani, YouTube kholo") is True
    assert detector.detect_in_text("shiwani ye gaana bajao") is True
    assert detector.detect_in_text("suno shivani") is True

    # Negative checks
    assert detector.detect_in_text("hello computer") is False
    assert detector.detect_in_text("open google chrome") is False


def test_wake_word_stripping():
    detector = LocalWakeWordDetector()

    q1 = detector.strip_wake_word("Shivani, open notepad")
    assert q1 == "open notepad"

    q2 = detector.strip_wake_word("Hey Shivani Chrome kholo")
    assert q2 == "Chrome kholo"


def test_local_wake_word_audio_energy():
    detector = LocalWakeWordDetector(energy_threshold=0.01)

    # Ambient silence (near zero energy)
    silence = np.zeros(1600, dtype=np.float32)
    assert detector.detect_in_audio(silence) is False

    # Audible speech burst (high energy sine wave)
    t = np.linspace(0, 0.1, 1600, endpoint=False)
    speech_signal = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    assert detector.detect_in_audio(speech_signal) is True


def test_mock_wake_word():
    mock_true = MockWakeWordDetector(triggered=True)
    assert mock_true.detect_in_audio(np.zeros(10)) is True

    mock_false = MockWakeWordDetector(triggered=False)
    assert mock_false.detect_in_audio(np.zeros(10)) is False
