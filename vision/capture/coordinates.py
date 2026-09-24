"""
SHIVANI Vision Coordinate Transformation Engine.
Provides rigorous mathematical mappings between:
  1. Physical Coordinates (Screenshot bitmap pixels)
  2. Logical Coordinates (Windows desktop scaling coordinates for OS inputs)
  3. Normalized Coordinates ([0.0, 1.0] unit box space)
"""

from typing import Tuple
from vision.models.types import (
    CoordinateSpace,
    Point,
    Size,
    BoundingBox,
    NormalizedBoundingBox,
    MonitorInfo,
)


def physical_to_logical_point(point: Point, scale_factor: float) -> Point:
    """Converts a point from physical screenshot pixel space to logical OS desktop space."""
    scale = max(0.1, scale_factor)
    return Point(
        x=point.x / scale,
        y=point.y / scale,
        coordinate_space=CoordinateSpace.LOGICAL,
    )


def logical_to_physical_point(point: Point, scale_factor: float) -> Point:
    """Converts a point from logical OS desktop space to physical screenshot pixel space."""
    scale = max(0.1, scale_factor)
    return Point(
        x=point.x * scale,
        y=point.y * scale,
        coordinate_space=CoordinateSpace.PHYSICAL,
    )


def physical_to_logical_box(box: BoundingBox, scale_factor: float) -> BoundingBox:
    """Transforms a bounding box from physical pixels to logical desktop coordinates."""
    scale = max(0.1, scale_factor)
    return BoundingBox(
        x=box.x / scale,
        y=box.y / scale,
        width=box.width / scale,
        height=box.height / scale,
        coordinate_space=CoordinateSpace.LOGICAL,
    )


def logical_to_physical_box(box: BoundingBox, scale_factor: float) -> BoundingBox:
    """Transforms a bounding box from logical desktop coordinates to physical pixels."""
    scale = max(0.1, scale_factor)
    return BoundingBox(
        x=box.x * scale,
        y=box.y * scale,
        width=box.width * scale,
        height=box.height * scale,
        coordinate_space=CoordinateSpace.PHYSICAL,
    )


def point_to_normalized(point: Point, display_size: Size) -> Tuple[float, float]:
    """Converts a pixel or logical point into normalized coordinates [0.0, 1.0]."""
    w = max(1.0, display_size.width)
    h = max(1.0, display_size.height)
    u = max(0.0, min(1.0, point.x / w))
    v = max(0.0, min(1.0, point.y / h))
    return (u, v)


def normalized_to_point(
    u: float,
    v: float,
    display_size: Size,
    target_space: CoordinateSpace = CoordinateSpace.LOGICAL
) -> Point:
    """Maps normalized [0.0, 1.0] coordinates to concrete display coordinates."""
    u_clamped = max(0.0, min(1.0, u))
    v_clamped = max(0.0, min(1.0, v))
    return Point(
        x=u_clamped * display_size.width,
        y=v_clamped * display_size.height,
        coordinate_space=target_space,
    )


def box_to_normalized(box: BoundingBox, display_size: Size) -> NormalizedBoundingBox:
    """Converts a bounding box into normalized [0.0, 1.0] unit bounds."""
    w = max(1.0, display_size.width)
    h = max(1.0, display_size.height)
    u_min = max(0.0, min(1.0, box.left / w))
    v_min = max(0.0, min(1.0, box.top / h))
    u_max = max(0.0, min(1.0, box.right / w))
    v_max = max(0.0, min(1.0, box.bottom / h))
    return NormalizedBoundingBox(
        u_min=u_min,
        v_min=v_min,
        u_max=u_max,
        v_max=v_max,
    )


def normalized_to_box(
    norm_box: NormalizedBoundingBox,
    display_size: Size,
    target_space: CoordinateSpace = CoordinateSpace.LOGICAL
) -> BoundingBox:
    """Expands normalized unit bounds to concrete pixel or logical bounding box."""
    x = norm_box.u_min * display_size.width
    y = norm_box.v_min * display_size.height
    w = norm_box.width * display_size.width
    h = norm_box.height * display_size.height
    return BoundingBox(
        x=x,
        y=y,
        width=w,
        height=h,
        coordinate_space=target_space,
    )


class CoordinateTransformer:
    """Helper for converting coordinates across spaces for a specific monitor configuration."""

    def __init__(self, monitor: MonitorInfo):
        self.monitor = monitor
        self.scale_factor = monitor.scale_factor
        self.logical_size = Size(width=float(monitor.width), height=float(monitor.height))
        self.physical_size = Size(
            width=float(monitor.width) * monitor.scale_factor,
            height=float(monitor.height) * monitor.scale_factor
        )

    def to_logical_point(self, point: Point) -> Point:
        if point.coordinate_space == CoordinateSpace.LOGICAL:
            return point
        return physical_to_logical_point(point, self.scale_factor)

    def to_physical_point(self, point: Point) -> Point:
        if point.coordinate_space == CoordinateSpace.PHYSICAL:
            return point
        return logical_to_physical_point(point, self.scale_factor)

    def to_logical_box(self, box: BoundingBox) -> BoundingBox:
        if box.coordinate_space == CoordinateSpace.LOGICAL:
            return box
        return physical_to_logical_box(box, self.scale_factor)

    def to_physical_box(self, box: BoundingBox) -> BoundingBox:
        if box.coordinate_space == CoordinateSpace.PHYSICAL:
            return box
        return logical_to_physical_box(box, self.scale_factor)
