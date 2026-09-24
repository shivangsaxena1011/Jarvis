"""
SHIVANI Layout Region and Semantic Container Analyzer.
Detects headers, sidebars, modals, toolbars, and visual flow.
"""

from typing import List, Dict, Optional
from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    Size,
    VisualElementType,
)
from vision.models.schemas import UIElement


class LayoutAnalyzer:
    """Analyzes spatial layout to identify functional screen regions."""

    def analyze_regions(
        self,
        elements: List[UIElement],
        screen_size: Size,
    ) -> Dict[str, List[UIElement]]:
        """Categorizes UI elements into functional regions."""
        w = screen_size.width
        h = screen_size.height

        regions: Dict[str, List[UIElement]] = {
            "header": [],
            "sidebar": [],
            "footer": [],
            "modal": [],
            "main_content": [],
        }

        # Thresholds
        top_threshold = h * 0.15
        bottom_threshold = h * 0.85
        left_threshold = w * 0.25

        for elem in elements:
            box = elem.bounding_box
            center = box.center

            # Modal check: Centered card with significant size but not full screen
            if (
                elem.element_type in (VisualElementType.MODAL, VisualElementType.CARD)
                or (box.width > w * 0.3 and box.height > h * 0.3 and box.width < w * 0.85 and box.height < h * 0.85)
            ):
                if abs(center.x - w / 2) < w * 0.2 and abs(center.y - h / 2) < h * 0.2:
                    regions["modal"].append(elem)
                    continue

            # Header check: In the top 15% of screen
            if center.y <= top_threshold:
                regions["header"].append(elem)
            # Footer check: In the bottom 15% of screen
            elif center.y >= bottom_threshold:
                regions["footer"].append(elem)
            # Sidebar check: On the left 25% of screen
            elif center.x <= left_threshold:
                regions["sidebar"].append(elem)
            else:
                regions["main_content"].append(elem)

        return regions

    def classify_flow(self, elements: List[UIElement]) -> str:
        """Determines predominant layout direction (vertical_stack, horizontal_row, grid)."""
        if len(elements) < 2:
            return "single"

        # Compare y variance vs x variance
        y_diffs = []
        x_diffs = []
        for i in range(len(elements) - 1):
            c1 = elements[i].bounding_box.center
            c2 = elements[i + 1].bounding_box.center
            y_diffs.append(abs(c2.y - c1.y))
            x_diffs.append(abs(c2.x - c1.x))

        avg_y = sum(y_diffs) / len(y_diffs)
        avg_x = sum(x_diffs) / len(x_diffs)

        if avg_y > avg_x * 2:
            return "vertical_stack"
        elif avg_x > avg_y * 2:
            return "horizontal_row"
        return "grid"
