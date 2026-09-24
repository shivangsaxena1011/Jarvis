"""
SHIVANI Visual Action Verifier.
Validates whether GUI interactions (clicks, typing, submissions) achieved their intended visual outcome.
"""

from typing import Dict, Any, Optional
from vision.models.schemas import VisualContext
from vision.verification.screen_diff import compute_screen_delta
from vision.verification.error_detector import VisualErrorDetector


class VisualVerifier:
    """Verifies screen state transitions following an agent execution step."""

    def __init__(self):
        self.error_detector = VisualErrorDetector()

    def verify_action_effect(
        self,
        before_context: VisualContext,
        after_context: VisualContext,
        expected_effect: str = "any_change",
        expected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validates post-action visual outcome.
        Returns:
            Dict containing verification status, confidence, screen delta, and diagnostics.
        """
        # 1. Compute delta between screenshots
        delta = compute_screen_delta(
            before_context.screenshot_path,
            after_context.screenshot_path,
        )

        # 2. Check for unexpected visual errors
        errors = self.error_detector.detect_errors(after_context)
        if errors:
            return {
                "verified": False,
                "confidence": 0.95,
                "error_detected": True,
                "errors": errors,
                "delta": delta.model_dump(),
                "details": f"Visual error occurred during action: {errors[0]['text']}",
            }

        # 3. Check expected effect
        if expected_effect == "any_change":
            is_ok = delta.has_changed
            return {
                "verified": is_ok,
                "confidence": 0.90 if is_ok else 0.70,
                "error_detected": False,
                "delta": delta.model_dump(),
                "details": "Screen state successfully updated." if is_ok else "No visual change detected on screen.",
            }

        elif expected_effect == "text_appeared" and expected_text:
            before_has_text = False
            after_has_text = False

            if before_context.ocr:
                before_has_text = len(before_context.ocr.find_text(expected_text)) > 0
            if after_context.ocr:
                after_has_text = len(after_context.ocr.find_text(expected_text)) > 0

            verified = after_has_text and not before_has_text
            return {
                "verified": verified,
                "confidence": 0.95,
                "error_detected": False,
                "delta": delta.model_dump(),
                "details": f"Expected text '{expected_text}' appeared on screen." if verified else f"Expected text '{expected_text}' not verified.",
            }

        elif expected_effect == "modal_opened":
            from vision.models.types import VisualElementType
            modals = [e for e in after_context.elements if e.element_type == VisualElementType.MODAL]
            verified = len(modals) > 0 and delta.has_changed
            return {
                "verified": verified,
                "confidence": 0.88,
                "error_detected": False,
                "delta": delta.model_dump(),
                "details": "Modal dialog opened on screen." if verified else "Modal dialog did not appear.",
            }

        return {
            "verified": delta.has_changed,
            "confidence": 0.80,
            "error_detected": False,
            "delta": delta.model_dump(),
            "details": delta.description,
        }
