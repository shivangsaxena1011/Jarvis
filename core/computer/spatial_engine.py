"""
SHIVANI Spatial Reasoning Engine (Phase 17).
Implements spatial relations between UI elements: above, below, left_of,
right_of, inside, contains, near, far, between, aligned_with, adjacent_to, etc.
"""

from __future__ import annotations
import math
from typing import List, Optional, Tuple
from core.computer.models import RectBounds, UIElement


class SpatialEngine:
    """Evaluates spatial relationships between UI elements on screen."""

    @staticmethod
    def distance(a: RectBounds, b: RectBounds) -> float:
        """Euclidean distance between element centers."""
        cx1, cy1 = a.center
        cx2, cy2 = b.center
        return math.hypot(cx1 - cx2, cy1 - cy2)

    @staticmethod
    def is_above(a: RectBounds, b: RectBounds) -> bool:
        """Element A is vertically above Element B."""
        return a.bottom <= b.top + 10 and not (a.right < b.left or a.left > b.right)

    @staticmethod
    def is_below(a: RectBounds, b: RectBounds) -> bool:
        """Element A is vertically below Element B."""
        return a.top >= b.bottom - 10 and not (a.right < b.left or a.left > b.right)

    @staticmethod
    def is_left_of(a: RectBounds, b: RectBounds) -> bool:
        """Element A is horizontally to the left of Element B."""
        return a.right <= b.left + 15 and not (a.bottom < b.top or a.top > b.bottom)

    @staticmethod
    def is_right_of(a: RectBounds, b: RectBounds) -> bool:
        """Element A is horizontally to the right of Element B."""
        return a.left >= b.right - 15 and not (a.bottom < b.top or a.top > b.bottom)

    @staticmethod
    def is_inside(a: RectBounds, b: RectBounds) -> bool:
        """Element A is entirely enclosed inside Element B."""
        return (
            a.left >= b.left - 2
            and a.top >= b.top - 2
            and a.right <= b.right + 2
            and a.bottom <= b.bottom + 2
        )

    @staticmethod
    def contains(a: RectBounds, b: RectBounds) -> bool:
        """Element A encloses Element B."""
        return SpatialEngine.is_inside(b, a)

    @staticmethod
    def is_near(a: RectBounds, b: RectBounds, max_distance: float = 160.0) -> bool:
        """Element A is within max_distance of Element B."""
        return SpatialEngine.distance(a, b) <= max_distance

    @staticmethod
    def is_far(a: RectBounds, b: RectBounds, min_distance: float = 300.0) -> bool:
        """Element A is further than min_distance from Element B."""
        return SpatialEngine.distance(a, b) >= min_distance

    @staticmethod
    def is_between(target: RectBounds, a: RectBounds, b: RectBounds) -> bool:
        """Target element is positioned between element A and element B."""
        tcx, tcy = target.center
        acx, acy = a.center
        bcx, bcy = b.center

        # Horizontal between
        if (min(acx, bcx) <= tcx <= max(acx, bcx)) and (abs(acy - bcy) < 50):
            return True
        # Vertical between
        if (min(acy, bcy) <= tcy <= max(acy, bcy)) and (abs(acx - bcx) < 50):
            return True
        return False

    @staticmethod
    def is_aligned_with(a: RectBounds, b: RectBounds, tolerance: int = 10) -> bool:
        """Elements share either horizontal or vertical alignment."""
        cx1, cy1 = a.center
        cx2, cy2 = b.center
        # Horizontally aligned (same Y) or Vertically aligned (same X)
        return abs(cy1 - cy2) <= tolerance or abs(cx1 - cx2) <= tolerance

    @staticmethod
    def is_overlapping(a: RectBounds, b: RectBounds) -> bool:
        """Elements intersect or overlap."""
        return not (
            a.right < b.left
            or a.left > b.right
            or a.bottom < b.top
            or a.top > b.bottom
        )

    @staticmethod
    def is_adjacent_to(a: RectBounds, b: RectBounds, max_gap: int = 25) -> bool:
        """Elements are directly adjacent with a small gap."""
        h_adjacent = abs(a.right - b.left) <= max_gap or abs(b.right - a.left) <= max_gap
        v_adjacent = abs(a.bottom - b.top) <= max_gap or abs(b.bottom - a.top) <= max_gap
        return (h_adjacent and abs(a.center[1] - b.center[1]) < 40) or (
            v_adjacent and abs(a.center[0] - b.center[0]) < 40
        )

    def filter_by_relation(
        self,
        candidates: List[UIElement],
        relation: str,
        reference: UIElement,
        **kwargs: Any,
    ) -> List[UIElement]:
        """
        Filters candidate elements matching a spatial predicate relative to reference.
        """
        matched = []
        ref_bounds = reference.bounds
        for cand in candidates:
            if cand.id == reference.id:
                continue
            b = cand.bounds
            rel = relation.lower().replace("-", "_")

            if rel == "above" and self.is_above(b, ref_bounds):
                matched.append(cand)
            elif rel == "below" and self.is_below(b, ref_bounds):
                matched.append(cand)
            elif rel == "left_of" and self.is_left_of(b, ref_bounds):
                matched.append(cand)
            elif rel == "right_of" and self.is_right_of(b, ref_bounds):
                matched.append(cand)
            elif rel == "inside" and self.is_inside(b, ref_bounds):
                matched.append(cand)
            elif rel == "contains" and self.contains(b, ref_bounds):
                matched.append(cand)
            elif rel == "near" and self.is_near(b, ref_bounds):
                matched.append(cand)
            elif rel == "far" and self.is_far(b, ref_bounds):
                matched.append(cand)
            elif rel == "aligned_with" and self.is_aligned_with(b, ref_bounds):
                matched.append(cand)
            elif rel == "adjacent_to" and self.is_adjacent_to(b, ref_bounds):
                matched.append(cand)
            elif rel == "overlapping" and self.is_overlapping(b, ref_bounds):
                matched.append(cand)

        # Sort by proximity to reference center
        matched.sort(key=lambda c: self.distance(c.bounds, ref_bounds))
        return matched
