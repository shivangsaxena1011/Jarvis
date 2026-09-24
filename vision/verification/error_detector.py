"""
SHIVANI Visual Error and Alert Detector.
Identifies error banners, crash dialogs, and failure prompts from OCR and visual styling.
"""

from typing import List, Dict, Any, Optional
import re
from PIL import Image

from vision.models.schemas import VisualContext, OCRResult
from vision.models.types import VisualElementType

ERROR_KEYWORDS = {
    "error",
    "failed",
    "failure",
    "exception",
    "crash",
    "access denied",
    "forbidden",
    "not found",
    "404",
    "500",
    "timed out",
    "unauthorized",
    "fatal",
    "cannot connect",
}


class VisualErrorDetector:
    """Scans visual screen context for error banners, crash prompts, and modal alerts."""

    def detect_errors(self, context: VisualContext) -> List[Dict[str, Any]]:
        """Finds any active visual error indicators on screen."""
        errors: List[Dict[str, Any]] = []

        if not context.ocr:
            return errors

        # 1. Search text lines for explicit error patterns
        for line in context.ocr.lines:
            line_lower = line.text.strip().lower()
            for kw in ERROR_KEYWORDS:
                if re.search(rf"\b{re.escape(kw)}\b", line_lower):
                    errors.append({
                        "type": "textual_error",
                        "keyword": kw,
                        "text": line.text,
                        "bounding_box": line.bounding_box.to_dict(),
                        "confidence": line.confidence,
                    })
                    break

        # 2. Check modal dialogs for error headers
        for elem in context.elements:
            if elem.element_type == VisualElementType.MODAL and elem.text:
                txt_lower = elem.text.lower()
                if any(kw in txt_lower for kw in ERROR_KEYWORDS):
                    errors.append({
                        "type": "error_dialog",
                        "text": elem.text,
                        "bounding_box": elem.bounding_box.to_dict(),
                        "confidence": elem.confidence,
                    })

        return errors
