"""
Tests for UI Element Detection, Visual Tree, and Layout Analysis.
"""

from PIL import Image, ImageDraw
from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    VisualElementType,
    Size,
)
from vision.models.schemas import UIElement
from vision.ui.element_detector import UIElementDetector
from vision.ui.ui_tree import VisualUITreeBuilder, VisualUITreeQuery
from vision.layout.layout_analyzer import LayoutAnalyzer
from vision.ocr.engine import MockOCRBackend


def test_ui_element_detection_with_synthetic_boxes():
    img = Image.new("RGB", (800, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Draw a simulated button rectangle
    draw.rectangle([200, 100, 320, 140], outline=(0, 0, 0), width=2)
    # Draw a simulated text box
    draw.rectangle([200, 200, 500, 240], outline=(0, 0, 0), width=2)

    detector = UIElementDetector(ocr_engine=MockOCRBackend())
    elements = detector.detect_elements(img)

    assert len(elements) >= 2
    types = [e.element_type for e in elements]
    assert VisualElementType.BUTTON in types or VisualElementType.TEXT in types


def test_visual_ui_tree_containment():
    builder = VisualUITreeBuilder()

    # Outer modal dialog
    modal = UIElement(
        id="modal_1",
        element_type=VisualElementType.MODAL,
        bounding_box=BoundingBox(x=100, y=100, width=600, height=400),
        text="Confirm Action",
    )
    # Button inside modal
    btn = UIElement(
        id="btn_ok",
        element_type=VisualElementType.BUTTON,
        bounding_box=BoundingBox(x=150, y=400, width=100, height=40),
        text="OK",
    )
    # Independent navbar button outside modal
    nav_btn = UIElement(
        id="btn_home",
        element_type=VisualElementType.BUTTON,
        bounding_box=BoundingBox(x=20, y=20, width=80, height=30),
        text="Home",
    )

    root = builder.build_tree([modal, btn, nav_btn])
    query = VisualUITreeQuery(root)

    # btn should be nested inside modal_1
    modal_node = next((c for c in root.children if c.element.id == "modal_1"), None)
    assert modal_node is not None
    assert any(c.element.id == "btn_ok" for c in modal_node.children)

    # Query tests
    found_buttons = query.find_by_type(VisualElementType.BUTTON)
    assert len(found_buttons) == 2

    ok_matches = query.find_by_text("OK")
    assert len(ok_matches) == 1
    assert ok_matches[0].id == "btn_ok"


def test_layout_analyzer_regions():
    analyzer = LayoutAnalyzer()
    screen_size = Size(width=1920, height=1080)

    header_btn = UIElement(
        id="nav",
        bounding_box=BoundingBox(x=100, y=30, width=120, height=40),
        text="Navigation",
    )
    sidebar_item = UIElement(
        id="side",
        bounding_box=BoundingBox(x=50, y=300, width=150, height=40),
        text="Inbox",
    )
    footer_text = UIElement(
        id="foot",
        bounding_box=BoundingBox(x=500, y=1000, width=300, height=30),
        text="Copyright 2026",
    )
    main_btn = UIElement(
        id="main_act",
        bounding_box=BoundingBox(x=800, y=500, width=200, height=50),
        text="Get Started",
    )

    regions = analyzer.analyze_regions([header_btn, sidebar_item, footer_text, main_btn], screen_size)
    assert any(e.id == "nav" for e in regions["header"])
    assert any(e.id == "side" for e in regions["sidebar"])
    assert any(e.id == "foot" for e in regions["footer"])
    assert any(e.id == "main_act" for e in regions["main_content"])
