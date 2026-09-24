"""
SHIVANI Privacy Redaction and Sensitive Region Masking.
Automatically redacts passwords, credit cards, OTPs, API keys, and private data
from screenshots before storage or external VLM submission.
"""

from typing import List, Tuple, Union, Optional
import re
from PIL import Image, ImageDraw

from vision.models.types import BoundingBox, CoordinateSpace
from vision.models.schemas import OCRResult, OCRWord

# Common sensitive regex patterns
SENSITIVE_PATTERNS = [
    # Credit Card numbers (13-19 digits, possibly hyphen or space separated)
    re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    # API tokens (e.g., sk_live..., ghp_..., AIzaSy...)
    re.compile(r"\b(?:sk_[a-zA-Z0-9_\-]{20,}|ghp_[a-zA-Z0-9]{30,}|AIzaSy[a-zA-Z0-9_\-]{30,})\b"),
    # OTP / 2FA codes (isolated 6-digit or 4-digit codes)
    re.compile(r"\b(?:otp|code|verification)[\s:]*([0-9]{4,8})\b", re.IGNORECASE),
    # Password bullets or asterisks
    re.compile(r"^[\u2022\*\.]{4,}$"),
]


class PrivacyRedactor:
    """Masks sensitive information from screenshots to protect user privacy."""

    def __init__(self, custom_exclusion_boxes: Optional[List[BoundingBox]] = None):
        self.custom_exclusion_boxes = custom_exclusion_boxes or []

    def find_sensitive_boxes(self, ocr_result: OCRResult) -> List[BoundingBox]:
        """Detects bounding boxes of sensitive OCR text."""
        sensitive_boxes: List[BoundingBox] = list(self.custom_exclusion_boxes)

        for word in ocr_result.words:
            # Check against patterns
            for pattern in SENSITIVE_PATTERNS:
                if pattern.search(word.text):
                    sensitive_boxes.append(word.bounding_box)
                    break

        return sensitive_boxes

    def redact_image(
        self,
        image: Union[str, Image.Image],
        sensitive_boxes: Optional[List[BoundingBox]] = None,
        save_path: Optional[str] = None,
    ) -> Tuple[str, Image.Image]:
        """
        Draws solid redaction masks over sensitive bounding boxes.
        Returns (save_path, redacted_image).
        """
        pil_img = Image.open(image) if isinstance(image, str) else image.copy()
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        draw = ImageDraw.Draw(pil_img)
        boxes = sensitive_boxes or []

        for box in boxes:
            # Add padding around the box
            pad = 4
            x0 = max(0, int(box.left) - pad)
            y0 = max(0, int(box.top) - pad)
            x1 = min(pil_img.width, int(box.right) + pad)
            y1 = min(pil_img.height, int(box.bottom) + pad)

            # Draw solid black rectangle over sensitive text
            draw.rectangle([x0, y0, x1, y1], fill=(20, 20, 20))

        if not save_path:
            import tempfile, time, os
            save_path = os.path.join(tempfile.gettempdir(), f"shivani_redacted_{int(time.time()*1000)}.png")

        pil_img.save(save_path, format="PNG")
        return (save_path, pil_img)
