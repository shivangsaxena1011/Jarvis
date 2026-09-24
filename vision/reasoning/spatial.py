"""
SHIVANI Spatial Reasoning Engine.
Calculates directional and topological relationships (ABOVE, BELOW, LEFT, RIGHT, INSIDE, NEAR)
between UI elements.
"""

from enum import Enum
from typing import List, Optional, Tuple
import math

from vision.models.types import BoundingBox, Point
from vision.models.schemas import UIElement


class SpatialRelation(str, Enum):
    ABOVE = "above"
    BELOW = "below"
    TO_LEFT_OF = "to_left_of"
    TO_RIGHT_OF = "to_right_of"
    INSIDE = "inside"
    NEAR = "near"


def distance_between_boxes(box_a: BoundingBox, box_b: BoundingBox) -> float:
    """Euclidean distance between center points of two boxes."""
    ca = box_a.center
    cb = box_b.center
    return math.sqrt((ca.x - cb.x) ** 2 + (ca.y - cb.y) ** 2)


def is_above(candidate: BoundingBox, reference: BoundingBox, max_horizontal_offset: float = 300.0) -> bool:
    """Checks if candidate is above reference box."""
    if candidate.bottom > reference.top + 5:
        return False
    # Check horizontal overlap or close horizontal alignment
    horizontal_overlap = not (candidate.right < reference.left or candidate.left > reference.right)
    horizontal_dist = abs(candidate.center.x - reference.center.x)
    return horizontal_overlap or (horizontal_dist < max_horizontal_offset)


def is_below(candidate: BoundingBox, reference: BoundingBox, max_horizontal_offset: float = 300.0) -> bool:
    """Checks if candidate is below reference box."""
    if candidate.top < reference.bottom - 5:
        return False
    horizontal_overlap = not (candidate.right < reference.left or candidate.left > reference.right)
    horizontal_dist = abs(candidate.center.x - reference.center.x)
    return horizontal_overlap or (horizontal_dist < max_horizontal_offset)


def is_to_left_of(candidate: BoundingBox, reference: BoundingBox, max_vertical_offset: float = 100.0) -> bool:
    """Checks if candidate is to the left of reference box."""
    if candidate.right > reference.left + 5:
        return False
    vertical_overlap = not (candidate.bottom < reference.top or candidate.top > reference.bottom)
    vertical_dist = abs(candidate.center.y - reference.center.y)
    return vertical_overlap or (vertical_dist < max_vertical_offset)


def is_to_right_of(candidate: BoundingBox, reference: BoundingBox, max_vertical_offset: float = 100.0) -> bool:
    """Checks if candidate is to the right of reference box."""
    if candidate.left < reference.right - 5:
        return False
    vertical_overlap = not (candidate.bottom < reference.top or candidate.top > reference.bottom)
    vertical_dist = abs(candidate.center.y - reference.center.y)
    return vertical_overlap or (vertical_dist < max_vertical_offset)


def is_inside(candidate: BoundingBox, container: BoundingBox) -> bool:
    """Checks if candidate is fully enclosed inside container."""
    return container.contains_box(candidate)


class SpatialReasoner:
    """Performs spatial filtering and relative queries on UI elements."""

    def filter_by_relation(
        self,
        reference: UIElement,
        candidates: List[UIElement],
        relation: SpatialRelation,
    ) -> List[Tuple[UIElement, float]]:
        """
        Filters candidates matching a spatial relationship to reference.
        Returns list of (candidate, distance) sorted ascending by distance.
        """
        matched: List[Tuple[UIElement, float]] = []
        ref_box = reference.bounding_box

        for cand in candidates:
            if cand.id == reference.id:
                continue

            c_box = cand.bounding_box
            is_match = False

            if relation == SpatialRelation.ABOVE:
                is_match = is_above(c_box, ref_box)
            elif relation == SpatialRelation.BELOW:
                is_match = is_below(c_box, ref_box)
            elif relation == SpatialRelation.TO_LEFT_OF:
                is_match = is_to_left_of(c_box, ref_box)
            elif relation == SpatialRelation.TO_RIGHT_OF:
                is_match = is_to_right_of(c_box, ref_box)
            elif relation == SpatialRelation.INSIDE:
                is_match = is_inside(c_box, ref_box)
            elif relation == SpatialRelation.NEAR:
                dist = distance_between_boxes(c_box, ref_box)
                if dist < 250.0:
                    is_match = True

            if is_match:
                dist = distance_between_boxes(c_box, ref_box)
                matched.append((cand, dist))

        matched.sort(key=lambda item: item[1])
        return matched

    def find_nearest(
        self,
        reference: UIElement,
        candidates: List[UIElement],
        relation: Optional[SpatialRelation] = None,
    ) -> Optional[UIElement]:
        """Finds the closest element satisfying the spatial relation."""
        if relation:
            matches = self.filter_by_relation(reference, candidates, relation)
            return matches[0][0] if matches else None

        # Nearest overall
        filtered = [c for c in candidates if c.id != reference.id]
        if not filtered:
            return None
        return min(filtered, key=lambda c: distance_between_boxes(c.bounding_box, reference.bounding_box))
