"""
Tests for Vision Primitive Types, Geometry, and Coordinate Transformations.
"""

import pytest
from vision.models.types import (
    CoordinateSpace,
    Point,
    Size,
    BoundingBox,
    NormalizedBoundingBox,
    MonitorInfo,
)
from vision.capture.coordinates import (
    physical_to_logical_point,
    logical_to_physical_point,
    physical_to_logical_box,
    logical_to_physical_box,
    point_to_normalized,
    normalized_to_point,
    box_to_normalized,
    normalized_to_box,
    CoordinateTransformer,
)


def test_bounding_box_geometry():
    box = BoundingBox(x=100.0, y=200.0, width=300.0, height=150.0)
    assert box.left == 100.0
    assert box.top == 200.0
    assert box.right == 400.0
    assert box.bottom == 350.0
    assert box.area == 45000.0
    assert box.center.x == 250.0
    assert box.center.y == 275.0


def test_bounding_box_containment_and_intersection():
    parent = BoundingBox(x=50.0, y=50.0, width=500.0, height=400.0)
    child = BoundingBox(x=100.0, y=100.0, width=200.0, height=100.0)
    outside = BoundingBox(x=600.0, y=100.0, width=50.0, height=50.0)

    assert parent.contains_box(child)
    assert not parent.contains_box(outside)
    assert parent.contains_point(Point(x=150.0, y=150.0))
    assert not parent.contains_point(Point(x=10.0, y=10.0))

    assert parent.overlaps(child)
    assert not parent.overlaps(outside)

    inter = parent.intersection(child)
    assert inter is not None
    assert inter.width == 200.0
    assert inter.height == 100.0

    iou = parent.iou(child)
    assert 0.0 < iou < 1.0


def test_coordinate_dpi_transformations():
    # 150% DPI scale factor
    scale = 1.5

    phys_pt = Point(x=1500.0, y=900.0, coordinate_space=CoordinateSpace.PHYSICAL)
    log_pt = physical_to_logical_point(phys_pt, scale)
    assert log_pt.x == 1000.0
    assert log_pt.y == 600.0
    assert log_pt.coordinate_space == CoordinateSpace.LOGICAL

    # Back to physical
    restored_pt = logical_to_physical_point(log_pt, scale)
    assert restored_pt.x == 1500.0
    assert restored_pt.y == 900.0
    assert restored_pt.coordinate_space == CoordinateSpace.PHYSICAL

    # Box transformation
    phys_box = BoundingBox(x=300.0, y=150.0, width=600.0, height=300.0, coordinate_space=CoordinateSpace.PHYSICAL)
    log_box = physical_to_logical_box(phys_box, scale)
    assert log_box.x == 200.0
    assert log_box.y == 100.0
    assert log_box.width == 400.0
    assert log_box.height == 200.0

    restored_box = logical_to_physical_box(log_box, scale)
    assert restored_box.x == 300.0
    assert restored_box.width == 600.0


def test_normalized_coordinate_mappings():
    display = Size(width=1920.0, height=1080.0)
    pt = Point(x=960.0, y=540.0)

    u, v = point_to_normalized(pt, display)
    assert abs(u - 0.5) < 1e-4
    assert abs(v - 0.5) < 1e-4

    mapped_pt = normalized_to_point(u, v, display)
    assert abs(mapped_pt.x - 960.0) < 1e-4
    assert abs(mapped_pt.y - 540.0) < 1e-4

    box = BoundingBox(x=480.0, y=270.0, width=960.0, height=540.0)
    norm_box = box_to_normalized(box, display)
    assert abs(norm_box.u_min - 0.25) < 1e-4
    assert abs(norm_box.v_min - 0.25) < 1e-4
    assert abs(norm_box.width - 0.5) < 1e-4
    assert abs(norm_box.height - 0.5) < 1e-4


def test_coordinate_transformer_helper():
    mon = MonitorInfo(
        id=1,
        name="Test_4K_Monitor",
        x=0,
        y=0,
        width=2560,
        height=1440,
        scale_factor=1.5,
    )
    transformer = CoordinateTransformer(mon)

    pt = Point(x=150.0, y=300.0, coordinate_space=CoordinateSpace.PHYSICAL)
    log = transformer.to_logical_point(pt)
    assert log.x == 100.0
    assert log.y == 200.0

    b = BoundingBox(x=100.0, y=100.0, width=200.0, height=200.0, coordinate_space=CoordinateSpace.LOGICAL)
    p_box = transformer.to_physical_box(b)
    assert p_box.width == 300.0
    assert p_box.height == 300.0
