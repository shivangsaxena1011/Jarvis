"""
Tests for Spatial Reasoning Engine (Directions, Containment, Proximity).
"""

from vision.models.types import BoundingBox, VisualElementType
from vision.models.schemas import UIElement
from vision.reasoning.spatial import (
    SpatialRelation,
    SpatialReasoner,
    is_above,
    is_below,
    is_to_left_of,
    is_to_right_of,
    distance_between_boxes,
)


def test_directional_predicates():
    top_box = BoundingBox(x=100, y=50, width=120, height=40)
    mid_box = BoundingBox(x=100, y=150, width=120, height=40)
    bot_box = BoundingBox(x=100, y=250, width=120, height=40)

    left_box = BoundingBox(x=20, y=150, width=60, height=40)
    right_box = BoundingBox(x=240, y=150, width=60, height=40)

    assert is_above(top_box, mid_box)
    assert not is_above(bot_box, mid_box)

    assert is_below(bot_box, mid_box)
    assert not is_below(top_box, mid_box)

    assert is_to_left_of(left_box, mid_box)
    assert not is_to_left_of(right_box, mid_box)

    assert is_to_right_of(right_box, mid_box)
    assert not is_to_right_of(left_box, mid_box)


def test_spatial_reasoner_filtering():
    reasoner = SpatialReasoner()

    ref = UIElement(
        id="ref_login",
        bounding_box=BoundingBox(x=200, y=200, width=100, height=40),
        text="Login",
    )
    above_elem = UIElement(
        id="elem_username",
        bounding_box=BoundingBox(x=200, y=120, width=180, height=40),
        text="Username",
    )
    below_elem = UIElement(
        id="elem_cancel",
        bounding_box=BoundingBox(x=200, y=280, width=100, height=40),
        text="Cancel",
    )
    right_elem = UIElement(
        id="elem_help",
        bounding_box=BoundingBox(x=340, y=200, width=60, height=40),
        text="Help",
    )

    candidates = [above_elem, below_elem, right_elem]

    below_matches = reasoner.filter_by_relation(ref, candidates, SpatialRelation.BELOW)
    assert len(below_matches) == 1
    assert below_matches[0][0].id == "elem_cancel"

    above_matches = reasoner.filter_by_relation(ref, candidates, SpatialRelation.ABOVE)
    assert len(above_matches) == 1
    assert above_matches[0][0].id == "elem_username"

    right_matches = reasoner.filter_by_relation(ref, candidates, SpatialRelation.TO_RIGHT_OF)
    assert len(right_matches) == 1
    assert right_matches[0][0].id == "elem_help"


def test_nearest_neighbor_resolution():
    reasoner = SpatialReasoner()

    ref = UIElement(
        id="ref",
        bounding_box=BoundingBox(x=100, y=100, width=50, height=50),
    )
    close_cand = UIElement(
        id="close",
        bounding_box=BoundingBox(x=100, y=180, width=50, height=50),
    )
    far_cand = UIElement(
        id="far",
        bounding_box=BoundingBox(x=100, y=400, width=50, height=50),
    )

    nearest = reasoner.find_nearest(ref, [far_cand, close_cand])
    assert nearest is not None
    assert nearest.id == "close"
