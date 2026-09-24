"""
Tests for Visual Verification, Screen Diffing, and Error Detection.
"""

from PIL import Image, ImageDraw
import tempfile, os

from vision.models.types import MonitorInfo, BoundingBox
from vision.models.schemas import VisualContext, OCRResult, OCRLine
from vision.verification.screen_diff import compute_screen_delta
from vision.verification.error_detector import VisualErrorDetector
from vision.verification.visual_verifier import VisualVerifier


def test_screen_delta_identical_and_modified():
    # Identical images
    img1 = Image.new("RGB", (400, 300), color=(200, 200, 200))
    img2 = Image.new("RGB", (400, 300), color=(200, 200, 200))

    delta_same = compute_screen_delta(img1, img2)
    assert not delta_same.has_changed
    assert delta_same.change_percentage == 0.0

    # Draw a change on img2
    draw = ImageDraw.Draw(img2)
    draw.rectangle([100, 100, 200, 150], fill=(255, 0, 0))

    delta_diff = compute_screen_delta(img1, img2)
    assert delta_diff.has_changed
    assert delta_diff.change_percentage > 0.0
    assert delta_diff.changed_region is not None
    assert delta_diff.changed_region.width >= 100
    assert delta_diff.changed_region.height >= 50


def test_visual_error_detection():
    detector = VisualErrorDetector()

    error_line = OCRLine(
        text="Fatal Error: Connection Timed Out",
        bounding_box=BoundingBox(x=100, y=100, width=300, height=30),
        confidence=0.98,
    )
    ocr = OCRResult(full_text="Fatal Error: Connection Timed Out", lines=[error_line])

    ctx = VisualContext(
        screenshot_path="/tmp/fake.png",
        timestamp=100.0,
        monitor=MonitorInfo(id=0),
        ocr=ocr,
    )

    errors = detector.detect_errors(ctx)
    assert len(errors) >= 1
    assert errors[0]["keyword"] in ("error", "fatal", "timed out")


def test_visual_action_verifier():
    verifier = VisualVerifier()

    t_dir = tempfile.gettempdir()
    p1 = os.path.join(t_dir, "test_v1.png")
    p2 = os.path.join(t_dir, "test_v2.png")

    img1 = Image.new("RGB", (200, 200), (255, 255, 255))
    img2 = Image.new("RGB", (200, 200), (255, 255, 255))
    draw = ImageDraw.Draw(img2)
    draw.rectangle([20, 20, 80, 80], fill=(0, 200, 0))

    img1.save(p1)
    img2.save(p2)

    ctx1 = VisualContext(screenshot_path=p1, timestamp=1.0, monitor=MonitorInfo(id=0))
    ctx2 = VisualContext(screenshot_path=p2, timestamp=2.0, monitor=MonitorInfo(id=0))

    res = verifier.verify_action_effect(ctx1, ctx2, expected_effect="any_change")
    assert res["verified"] is True
    assert res["error_detected"] is False
