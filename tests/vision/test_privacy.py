"""
Tests for Privacy Redaction Subsystem.
"""

from PIL import Image
import numpy as np
import tempfile, os

from vision.models.types import BoundingBox
from vision.models.schemas import OCRResult, OCRWord
from vision.privacy.redaction import PrivacyRedactor


def test_sensitive_pattern_detection():
    redactor = PrivacyRedactor()

    words = [
        OCRWord(text="Welcome", bounding_box=BoundingBox(x=10, y=10, width=50, height=20)),
        OCRWord(text="4532-1234-5678-9012", bounding_box=BoundingBox(x=100, y=50, width=150, height=20)), # CC
        OCRWord(text="••••••••", bounding_box=BoundingBox(x=100, y=100, width=80, height=20)), # Password mask
        OCRWord(text="sk_test_51Abcdef12345678901234567", bounding_box=BoundingBox(x=100, y=150, width=200, height=20)), # API key
    ]
    ocr = OCRResult(full_text="", words=words)

    sensitive_boxes = redactor.find_sensitive_boxes(ocr)
    assert len(sensitive_boxes) == 3


def test_image_redaction_masking():
    redactor = PrivacyRedactor()

    # White image
    img = Image.new("RGB", (300, 200), color=(255, 255, 255))
    target_box = BoundingBox(x=50, y=50, width=100, height=50)

    save_path, redacted_img = redactor.redact_image(img, [target_box])

    assert os.path.exists(save_path)
    # Check pixels in redacted region are dark/black
    arr = np.array(redacted_img)
    # Sample center pixel of target box: (100, 75)
    center_pixel = arr[75, 100]
    assert center_pixel[0] < 50
    assert center_pixel[1] < 50
    assert center_pixel[2] < 50

    # Outside pixel should still be white (255, 255, 255)
    outside_pixel = arr[10, 10]
    assert outside_pixel[0] == 255
