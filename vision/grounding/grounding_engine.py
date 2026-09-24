"""
SHIVANI Target Grounding Engine.
Resolves natural language GUI intents to exact screen elements and click coordinates.
"""

from typing import List, Optional, Tuple
import re

from vision.models.types import (
    Point,
    VisualElementType,
)
from vision.models.schemas import UIElement, VisualContext
from vision.reasoning.spatial import SpatialRelation, SpatialReasoner
from vision.ocr.fuzzy import fuzzy_match_ratio


class GroundingEngine:
    """Translates high-level natural language user queries into concrete screen coordinates."""

    def __init__(self):
        self.reasoner = SpatialReasoner()

    def ground(
        self,
        query: str,
        context: VisualContext,
    ) -> Tuple[Optional[UIElement], Optional[Point], float]:
        """
        Grounds natural language intent against visual context elements.
        Returns:
            (Best UIElement, Logical Click Point, Confidence Score)
        """
        if not context.elements:
            return (None, None, 0.0)

        q_lower = query.strip().lower()

        # Check for spatial patterns: "[target] (below|above|left of|right of|next to) [landmark]"
        spatial_pattern = r"^(.*?)\s+(below|under|above|to the left of|left of|to the right of|right of|next to|beside)\s+(.*)$"
        match = re.match(spatial_pattern, q_lower)

        if match:
            target_desc = match.group(1).strip()
            rel_str = match.group(2).strip()
            landmark_desc = match.group(3).strip()

            relation = self._parse_spatial_relation(rel_str)
            return self._ground_spatial_query(target_desc, relation, landmark_desc, context.elements)

        # Non-spatial direct target grounding
        return self._ground_direct_query(q_lower, context.elements)

    def _parse_spatial_relation(self, rel_str: str) -> SpatialRelation:
        if rel_str in ("below", "under"):
            return SpatialRelation.BELOW
        elif rel_str in ("above",):
            return SpatialRelation.ABOVE
        elif "left" in rel_str:
            return SpatialRelation.TO_LEFT_OF
        elif "right" in rel_str:
            return SpatialRelation.TO_RIGHT_OF
        return SpatialRelation.NEAR

    def _ground_direct_query(
        self,
        target_query: str,
        elements: List[UIElement],
    ) -> Tuple[Optional[UIElement], Optional[Point], float]:
        """Finds direct best matching element by text and type."""
        best_elem: Optional[UIElement] = None
        best_score = 0.0

        for elem in elements:
            score = 0.0
            # Text similarity score (up to 0.70)
            if elem.text:
                ratio = fuzzy_match_ratio(target_query, elem.text)
                score += ratio * 0.70

            # Element type boost (up to 0.30)
            if "button" in target_query and elem.element_type == VisualElementType.BUTTON:
                score += 0.30
            elif "input" in target_query and elem.element_type == VisualElementType.INPUT:
                score += 0.30
            elif "checkbox" in target_query and elem.element_type == VisualElementType.CHECKBOX:
                score += 0.30

            if score > best_score:
                best_score = score
                best_elem = elem

        if best_elem and best_score >= 0.40:
            click_pt = Point(
                x=best_elem.bounding_box.center.x,
                y=best_elem.bounding_box.center.y,
                coordinate_space=best_elem.bounding_box.coordinate_space,
            )
            return (best_elem, click_pt, min(1.0, best_score))

        return (None, None, 0.0)

    def _ground_spatial_query(
        self,
        target_desc: str,
        relation: SpatialRelation,
        landmark_desc: str,
        elements: List[UIElement],
    ) -> Tuple[Optional[UIElement], Optional[Point], float]:
        """Resolves target relative to a spatial landmark."""
        # 1. Ground landmark
        landmark, _, landmark_conf = self._ground_direct_query(landmark_desc, elements)
        if not landmark:
            return (None, None, 0.0)

        # 2. Filter candidates matching spatial relation to landmark
        candidates = self.reasoner.filter_by_relation(landmark, elements, relation)
        if not candidates:
            return (None, None, 0.0)

        # 3. Score candidates by target description (e.g. input, button)
        best_cand: Optional[UIElement] = None
        best_score = 0.0

        for cand, dist in candidates:
            score = 0.50  # Base spatial match score
            # Proximity boost (closer gets higher score)
            proximity_factor = max(0.0, 1.0 - (dist / 600.0))
            score += proximity_factor * 0.20

            # Target type check
            if "input" in target_desc and cand.element_type == VisualElementType.INPUT:
                score += 0.30
            elif "button" in target_desc and cand.element_type == VisualElementType.BUTTON:
                score += 0.30
            elif cand.text and target_desc in cand.text.lower():
                score += 0.30

            if score > best_score:
                best_score = score
                best_cand = cand

        if best_cand:
            click_pt = Point(
                x=best_cand.bounding_box.center.x,
                y=best_cand.bounding_box.center.y,
                coordinate_space=best_cand.bounding_box.coordinate_space,
            )
            final_conf = min(1.0, best_score * landmark_conf)
            return (best_cand, click_pt, final_conf)

        return (None, None, 0.0)
