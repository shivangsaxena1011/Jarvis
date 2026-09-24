"""
SHIVANI Vision Service Facade.
Central access point coordinating Screen Capture, OCR, UI Element Detection,
Spatial Reasoning, Grounding, Verification, and Privacy Redaction.
"""

from __future__ import annotations
from typing import Optional, Tuple, Dict, Any, List, Union
import time
from PIL import Image

from vision.models.types import (
    Point,
    BoundingBox,
    CoordinateSpace,
    MonitorInfo,
)
from vision.models.schemas import (
    UIElement,
    UITreeNode,
    OCRResult,
    VisualContext,
    VisualDelta,
)
from vision.capture.screen_capture import ScreenCaptureEngine
from vision.capture.window_capture import WindowCaptureEngine
from vision.capture.coordinates import CoordinateTransformer
from vision.ocr.engine import OCREngine, create_default_ocr_engine
from vision.ui.element_detector import UIElementDetector
from vision.ui.ui_tree import VisualUITreeBuilder
from vision.grounding.grounding_engine import GroundingEngine
from vision.verification.visual_verifier import VisualVerifier
from vision.privacy.redaction import PrivacyRedactor
from vision.overlay.debug_overlay import VisualDebugOverlay
from vision.providers.vlm import VisionLanguageModel, create_vlm_provider


class VisionService:
    """Unified facade managing all Phase 10 computer vision intelligence capabilities."""

    def __init__(
        self,
        ocr_engine: Optional[OCREngine] = None,
        vlm_provider: Optional[VisionLanguageModel] = None,
    ):
        self.screen_capture = ScreenCaptureEngine()
        self.window_capture = WindowCaptureEngine(self.screen_capture)
        self.ocr_engine = ocr_engine or create_default_ocr_engine()
        self.element_detector = UIElementDetector(self.ocr_engine)
        self.tree_builder = VisualUITreeBuilder()
        self.grounding_engine = GroundingEngine()
        self.verifier = VisualVerifier()
        self.redactor = PrivacyRedactor()
        self.overlay = VisualDebugOverlay()
        self.vlm = vlm_provider or create_vlm_provider("mock")

    def capture_and_understand(
        self,
        monitor_id: Optional[int] = None,
        save_path: Optional[str] = None,
    ) -> VisualContext:
        """
        Captures the screen and produces a rich, fused VisualContext
        including OCR, detected UI elements, and hierarchical UI tree.
        """
        img_path, monitor, pil_img = self.screen_capture.capture_full_screen(
            monitor_id=monitor_id,
            save_path=save_path,
        )

        win_info = self.window_capture.get_active_window_info()

        # Run OCR pass
        ocr_res = self.ocr_engine.extract(pil_img)

        # Run UI element detection pass
        elements = self.element_detector.detect_elements(pil_img, ocr_res)

        # Transform element bounding boxes to Logical coordinates if they are in Physical
        transformer = CoordinateTransformer(monitor)
        for elem in elements:
            if elem.bounding_box.coordinate_space == CoordinateSpace.PHYSICAL:
                elem.bounding_box = transformer.to_logical_box(elem.bounding_box)

        # Build hierarchical containment tree
        root_bounds = BoundingBox(
            x=0,
            y=0,
            width=float(monitor.width),
            height=float(monitor.height),
            coordinate_space=CoordinateSpace.LOGICAL,
        )
        ui_tree = self.tree_builder.build_tree(elements, root_bounds=root_bounds)

        context = VisualContext(
            screenshot_path=img_path,
            timestamp=time.time(),
            monitor=monitor,
            active_window=win_info,
            ocr=ocr_res,
            elements=elements,
            ui_tree=ui_tree,
        )
        return context

    def locate_target(
        self,
        query: str,
        context: Optional[VisualContext] = None,
    ) -> Tuple[Optional[UIElement], Optional[Point], float]:
        """
        Grounds a user instruction or target name to a screen element and click coordinate.
        """
        ctx = context or self.capture_and_understand()
        return self.grounding_engine.ground(query, ctx)

    def verify_action(
        self,
        before_context: VisualContext,
        after_context: VisualContext,
        expected_effect: str = "any_change",
        expected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Verifies state transition between pre-action and post-action visual states."""
        return self.verifier.verify_action_effect(
            before_context=before_context,
            after_context=after_context,
            expected_effect=expected_effect,
            expected_text=expected_text,
        )

    def redact_sensitive_screen(
        self,
        image_or_context: Union[str, VisualContext],
        save_path: Optional[str] = None,
    ) -> Tuple[str, Image.Image]:
        """Masks private credentials (passwords, OTPs, credit cards) from screen image."""
        if isinstance(image_or_context, VisualContext):
            img_path = image_or_context.screenshot_path
            ocr_res = image_or_context.ocr or self.ocr_engine.extract(img_path)
        else:
            img_path = image_or_context
            ocr_res = self.ocr_engine.extract(img_path)

        sensitive_boxes = self.redactor.find_sensitive_boxes(ocr_res)
        return self.redactor.redact_image(img_path, sensitive_boxes, save_path=save_path)

    def create_debug_overlay(self, context: VisualContext, save_path: Optional[str] = None) -> str:
        """Renders color-coded debug bounding boxes and returns saved overlay image path."""
        path, _ = self.overlay.render_overlay(
            context.screenshot_path,
            context.elements,
            save_path=save_path,
        )
        return path


_global_vision_service: Optional[VisionService] = None


def get_vision_service() -> VisionService:
    """Global singleton accessor for VisionService."""
    global _global_vision_service
    if _global_vision_service is None:
        _global_vision_service = VisionService()
    return _global_vision_service
