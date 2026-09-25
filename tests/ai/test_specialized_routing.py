"""Unit tests for Multimodal Specialized Routing (Vision, OCR, Speech)."""

import pytest
from core.ai.models import PrivacyLevel
from core.ai.specialized_routing import (
    MultimodalRouter,
    OCRRouter,
    SpeechRouter,
    VisionRouter,
)


def test_vision_router_prefers_accessibility_tree():
    engine, reason = VisionRouter.select_vision_engine(
        has_accessibility_tree=True,
        requires_image_comprehension=False,
    )
    assert engine == "accessibility_tree"
    assert "UIAutomation" in reason


def test_vision_router_private_image_routes_local():
    engine, reason = VisionRouter.select_vision_engine(
        has_accessibility_tree=False,
        requires_image_comprehension=True,
        privacy_level=PrivacyLevel.CRITICAL,
    )
    assert engine == "local_vision_llava"


def test_vision_router_public_complex_diagram_routes_cloud():
    engine, reason = VisionRouter.select_vision_engine(
        has_accessibility_tree=False,
        requires_image_comprehension=True,
        privacy_level=PrivacyLevel.PUBLIC,
    )
    assert engine == "cloud_vision_gemini"


def test_ocr_router_private_document_routes_local():
    engine, reason = OCRRouter.select_ocr_engine(
        is_handwritten=False,
        privacy_level=PrivacyLevel.SENSITIVE,
    )
    assert engine == "local_paddle_ocr"


def test_ocr_router_handwritten_document_routes_cloud():
    engine, reason = OCRRouter.select_ocr_engine(
        is_handwritten=True,
        privacy_level=PrivacyLevel.PUBLIC,
    )
    assert engine == "cloud_vision_ocr"


def test_speech_router_stt_and_tts():
    # STT local
    stt_local = SpeechRouter.select_stt(privacy_level=PrivacyLevel.PRIVATE)
    assert stt_local == "faster_whisper_local"

    # TTS local
    tts_local = SpeechRouter.select_tts(prefer_local=True)
    assert tts_local == "piper_tts_local"

    # TTS cloud
    tts_cloud = SpeechRouter.select_tts(prefer_local=False)
    assert tts_cloud == "cloud_tts"


def test_multimodal_router_facade():
    mm = MultimodalRouter()
    engine, _ = mm.route_vision(has_accessibility_tree=True)
    assert engine == "accessibility_tree"

    ocr_eng, _ = mm.route_ocr(is_handwritten=False)
    assert ocr_eng == "local_paddle_ocr"

    stt = mm.route_stt(prefer_local=True)
    assert stt == "faster_whisper_local"
