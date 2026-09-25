"""Specialized Multimodal Routing (Vision, OCR, STT, TTS) for Phase 19.

Intelligently avoids expensive vision calls by preferring accessibility trees and local OCR
for structured computer automation, and routes speech engines based on privacy and latency.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

from core.ai.models import PrivacyLevel

logger = logging.getLogger("shivani.ai.specialized")


class VisionRouter:
    """Routes visual desktop comprehension to the most efficient engine."""

    @classmethod
    def select_vision_engine(
        cls,
        has_accessibility_tree: bool,
        requires_image_comprehension: bool = False,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
    ) -> Tuple[str, str]:
        """Determine whether to use Accessibility Tree, Local OCR, or Vision Model.

        Returns:
            Tuple of (engine_name, rationale)
        """
        # 1. If structured accessibility tree is available and user just wants UI interaction
        if has_accessibility_tree and not requires_image_comprehension:
            return (
                "accessibility_tree",
                "Using Windows UIAutomation tree directly (zero model latency, exact coordinates).",
            )

        # 2. If privacy is SENSITIVE or CRITICAL -> local vision / OCR only
        if privacy_level in (PrivacyLevel.CRITICAL, PrivacyLevel.SENSITIVE, PrivacyLevel.PRIVATE):
            if requires_image_comprehension:
                return ("local_vision_llava", "Private desktop image routed to local vision model.")
            return ("local_ocr_tesseract", "Private screen text extracted via local OCR.")

        # 3. For complex visual diagrams or image queries where cloud is permitted
        if requires_image_comprehension:
            return ("cloud_vision_gemini", "Complex diagram/photo comprehension routed to cloud vision.")

        return ("accessibility_tree", "Defaulting to high-accuracy accessibility tree.")


class OCRRouter:
    """Routes document text extraction between local PaddleOCR/Tesseract and cloud OCR."""

    @classmethod
    def select_ocr_engine(
        cls,
        is_handwritten: bool = False,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
    ) -> Tuple[str, str]:
        if privacy_level in (PrivacyLevel.CRITICAL, PrivacyLevel.SENSITIVE, PrivacyLevel.PRIVATE):
            return ("local_paddle_ocr", "Private document routed to local OCR engine.")

        if is_handwritten:
            return ("cloud_vision_ocr", "Handwritten or low-contrast document routed to cloud OCR.")

        return ("local_paddle_ocr", "Standard printed document processed with local OCR.")


class SpeechRouter:
    """Routes STT and TTS engines based on latency targets and privacy."""

    @classmethod
    def select_stt(cls, privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC, prefer_local: bool = True) -> str:
        if prefer_local or privacy_level != PrivacyLevel.PUBLIC:
            return "faster_whisper_local"
        return "cloud_stt"

    @classmethod
    def select_tts(cls, prefer_local: bool = True) -> str:
        if prefer_local:
            return "piper_tts_local"
        return "cloud_tts"


class MultimodalRouter:
    """Unified router for vision, OCR, and speech modality decisions."""

    def __init__(self):
        self.vision = VisionRouter()
        self.ocr = OCRRouter()
        self.speech = SpeechRouter()

    def route_vision(
        self,
        has_accessibility_tree: bool,
        requires_image_comprehension: bool = False,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
    ) -> Tuple[str, str]:
        return self.vision.select_vision_engine(has_accessibility_tree, requires_image_comprehension, privacy_level)

    def route_ocr(
        self,
        is_handwritten: bool = False,
        privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC,
    ) -> Tuple[str, str]:
        return self.ocr.select_ocr_engine(is_handwritten, privacy_level)

    def route_stt(self, privacy_level: PrivacyLevel = PrivacyLevel.PUBLIC, prefer_local: bool = True) -> str:
        return self.speech.select_stt(privacy_level, prefer_local)

    def route_tts(self, prefer_local: bool = True) -> str:
        return self.speech.select_tts(prefer_local)

