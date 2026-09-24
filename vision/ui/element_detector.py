"""
SHIVANI Visual UI Element Detector.
Detects buttons, input fields, checkboxes, modals, cards, and text controls
via visual heuristics and OCR fusion.
"""

from __future__ import annotations
from typing import List, Optional, Union
import numpy as np
from PIL import Image

from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    VisualElementType,
    VisualState,
)
from vision.models.schemas import UIElement, OCRResult, OCRWord
from vision.ocr.engine import OCREngine, create_default_ocr_engine


class UIElementDetector:
    """Detects UI controls and components from screenshot images and OCR."""

    def __init__(self, ocr_engine: Optional[OCREngine] = None):
        self.ocr_engine = ocr_engine or create_default_ocr_engine()

    def detect_elements(
        self,
        image: Union[str, Image.Image],
        ocr_result: Optional[OCRResult] = None,
    ) -> List[UIElement]:
        """Runs visual element detection and fuses OCR text with detected controls."""
        pil_img = Image.open(image) if isinstance(image, str) else image
        if pil_img.mode != "RGB":
            pil_img = pil_img.convert("RGB")

        if ocr_result is None:
            ocr_result = self.ocr_engine.extract(pil_img)

        elements: List[UIElement] = []

        # 1. Generate elements directly from OCR words and lines
        # Group text words into buttons or inputs based on semantics
        button_keywords = {"ok", "cancel", "submit", "save", "next", "back", "login", "sign in", "apply", "close", "delete", "search", "send"}

        for line in ocr_result.lines:
            text_lower = line.text.strip().lower()
            elem_type = VisualElementType.TEXT

            if any(text_lower == kw or text_lower.startswith(kw + " ") for kw in button_keywords):
                elem_type = VisualElementType.BUTTON

            elements.append(
                UIElement(
                    element_type=elem_type,
                    bounding_box=line.bounding_box,
                    text=line.text,
                    confidence=line.confidence,
                    attributes={"source": "ocr_line"},
                )
            )

        # 2. Visual contour/box detection using numpy array
        visual_boxes = self._detect_rectangles_from_image(pil_img)

        for box, guessed_type in visual_boxes:
            # Check if this box overlaps/encloses any existing OCR text
            contained_words = [
                w for w in ocr_result.words
                if box.contains_box(w.bounding_box) or box.iou(w.bounding_box) > 0.3
            ]

            label_text = " ".join(w.text for w in contained_words) if contained_words else None

            # Refine element type
            final_type = guessed_type
            if label_text:
                lbl_lower = label_text.strip().lower()
                if any(lbl_lower == kw or lbl_lower.startswith(kw) for kw in button_keywords):
                    final_type = VisualElementType.BUTTON

            # Avoid exact duplicate bounding boxes
            if not any(e.bounding_box.iou(box) > 0.8 for e in elements):
                elements.append(
                    UIElement(
                        element_type=final_type,
                        bounding_box=box,
                        text=label_text,
                        confidence=0.88,
                        attributes={"source": "visual_contour"},
                    )
                )

        return elements

    def _detect_rectangles_from_image(self, img: Image.Image) -> List[tuple[BoundingBox, VisualElementType]]:
        """
        Fast heuristic box detection using intensity gradients and edge contrast.
        Identifies input boxes, buttons, cards, and modal dialogs.
        """
        boxes: List[tuple[BoundingBox, VisualElementType]] = []
        w, h = img.size

        # Downsample for fast processing if huge
        scale = 1.0
        if w > 1920 or h > 1080:
            scale = 0.5
            proc_img = img.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)
        else:
            proc_img = img

        arr = np.array(proc_img.convert("L"), dtype=np.int32)
        pw, ph = proc_img.size

        if pw < 50 or ph < 50:
            return boxes

        # Intensity gradients
        dx = np.abs(arr[:, 1:] - arr[:, :-1])
        dy = np.abs(arr[1:, :] - arr[:-1, :])

        edge_x = dx > 35
        edge_y = dy > 35

        def get_contiguous_segments(indices: np.ndarray, min_len: int = 40, max_len: int = 700):
            if len(indices) == 0:
                return []
            segments = []
            start = int(indices[0])
            prev = int(indices[0])
            for x in indices[1:]:
                xi = int(x)
                if xi - prev <= 2:
                    prev = xi
                else:
                    if min_len <= (prev - start) <= max_len:
                        segments.append((start, prev))
                    start = xi
                    prev = xi
            if min_len <= (prev - start) <= max_len:
                segments.append((start, prev))
            return segments

        # Scan horizontal candidate lines
        step = 5
        seen_regions = set()
        for y in range(10, ph - 25, step):
            row = edge_y[min(y, edge_y.shape[0] - 1), :]
            transitions = np.where(row)[0]
            if len(transitions) == 0:
                continue

            segments = get_contiguous_segments(transitions, min_len=40, max_len=700)
            for x1, x2 in segments:
                width = x2 - x1
                # Check candidate heights
                for height in range(25, 120, 5):
                    by = y + height
                    if by >= edge_y.shape[0]:
                        break
                    bot_row = edge_y[by, :]
                    bot_transitions = np.where(bot_row)[0]
                    bot_segments = get_contiguous_segments(bot_transitions, min_len=30, max_len=750)
                    has_parallel = any(abs(bx1 - x1) <= 15 and abs(bx2 - x2) <= 15 for bx1, bx2 in bot_segments)

                    if has_parallel:
                        region_key = (int(x1 / 15), int(y / 15), int(width / 20), int(height / 10))
                        if region_key not in seen_regions:
                            seen_regions.add(region_key)
                            orig_box = BoundingBox(
                                x=float(x1 / scale),
                                y=float(y / scale),
                                width=float(width / scale),
                                height=float(height / scale),
                                coordinate_space=CoordinateSpace.PHYSICAL,
                            )
                            elem_type = (
                                VisualElementType.INPUT
                                if width > 180 and height >= 35
                                else VisualElementType.BUTTON
                            )
                            boxes.append((orig_box, elem_type))
                        break

            if len(boxes) >= 50:
                break

        return boxes
