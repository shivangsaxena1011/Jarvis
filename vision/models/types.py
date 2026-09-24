"""
SHIVANI Vision Primitive Types and Geometry.
"""

from __future__ import annotations
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class CoordinateSpace(str, Enum):
    """Reference coordinate system for display and GUI spatial calculations."""
    PHYSICAL = "physical"      # Raw pixel bitmap of the screen screenshot (e.g., 3840x2160)
    LOGICAL = "logical"        # Win32 OS desktop coordinate space scaled by DPI (e.g., 2560x1440)
    NORMALIZED = "normalized"  # Relative float coordinates in [0.0, 1.0] across display dimensions


class VisualElementType(str, Enum):
    """Semantic category of detected UI elements."""
    BUTTON = "button"
    INPUT = "input"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    DROPDOWN = "dropdown"
    ICON = "icon"
    MODAL = "modal"
    CARD = "card"
    TABLE = "table"
    TEXT = "text"
    IMAGE = "image"
    CONTAINER = "container"
    HEADER = "header"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    LINK = "link"
    TAB = "tab"
    UNKNOWN = "unknown"


class VisualState(str, Enum):
    """Visual interaction state of an element."""
    NORMAL = "normal"
    HOVERED = "hovered"
    FOCUSED = "focused"
    DISABLED = "disabled"
    CHECKED = "checked"
    ACTIVE = "active"
    HIDDEN = "hidden"


class Point(BaseModel):
    """A 2D spatial coordinate point."""
    x: float
    y: float
    coordinate_space: CoordinateSpace = CoordinateSpace.LOGICAL

    def as_tuple(self) -> Tuple[float, float]:
        return (self.x, self.y)

    def as_int_tuple(self) -> Tuple[int, int]:
        return (int(round(self.x)), int(round(self.y)))


class Size(BaseModel):
    """Dimensions of a 2D bounding area."""
    width: float
    height: float

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)


class BoundingBox(BaseModel):
    """Rectangular bounding box in pixel or logical coordinate space."""
    x: float
    y: float
    width: float
    height: float
    coordinate_space: CoordinateSpace = CoordinateSpace.LOGICAL

    @property
    def left(self) -> float:
        return self.x

    @property
    def top(self) -> float:
        return self.y

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Point:
        return Point(
            x=self.x + self.width / 2.0,
            y=self.y + self.height / 2.0,
            coordinate_space=self.coordinate_space
        )

    @property
    def area(self) -> float:
        return max(0.0, self.width) * max(0.0, self.height)

    def contains_point(self, point: Point) -> bool:
        """Determines if a given point is enclosed inside the bounding box."""
        return (
            self.left <= point.x <= self.right
            and self.top <= point.y <= self.bottom
        )

    def contains_box(self, other: BoundingBox) -> bool:
        """Determines if this bounding box fully encloses another box."""
        return (
            self.left <= other.left
            and self.top <= other.top
            and self.right >= other.right
            and self.bottom >= other.bottom
        )

    def overlaps(self, other: BoundingBox) -> bool:
        """Checks if two bounding boxes intersect."""
        return not (
            self.right < other.left
            or self.left > other.right
            or self.bottom < other.top
            or self.top > other.bottom
        )

    def intersection(self, other: BoundingBox) -> Optional[BoundingBox]:
        """Returns the intersecting sub-box or None if non-overlapping."""
        ix1 = max(self.left, other.left)
        iy1 = max(self.top, other.top)
        ix2 = min(self.right, other.right)
        iy2 = min(self.bottom, other.bottom)

        if ix2 >= ix1 and iy2 >= iy1:
            return BoundingBox(
                x=ix1,
                y=iy1,
                width=ix2 - ix1,
                height=iy2 - iy1,
                coordinate_space=self.coordinate_space,
            )
        return None

    def iou(self, other: BoundingBox) -> float:
        """Intersection over Union (IoU) metric in [0.0, 1.0]."""
        inter = self.intersection(other)
        if not inter:
            return 0.0
        inter_area = inter.area
        union_area = self.area + other.area - inter_area
        if union_area <= 0:
            return 0.0
        return inter_area / union_area

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "coordinate_space": self.coordinate_space.value,
        }

    def to_int_dict(self) -> Dict[str, int]:
        return {
            "x": int(round(self.x)),
            "y": int(round(self.y)),
            "width": int(round(self.width)),
            "height": int(round(self.height)),
        }


class NormalizedBoundingBox(BaseModel):
    """Normalized bounding box with coordinates bounded in [0.0, 1.0]."""
    u_min: float = Field(ge=0.0, le=1.0)
    v_min: float = Field(ge=0.0, le=1.0)
    u_max: float = Field(ge=0.0, le=1.0)
    v_max: float = Field(ge=0.0, le=1.0)

    @property
    def width(self) -> float:
        return max(0.0, self.u_max - self.u_min)

    @property
    def height(self) -> float:
        return max(0.0, self.v_max - self.v_min)

    @property
    def center(self) -> Tuple[float, float]:
        return ((self.u_min + self.u_max) / 2.0, (self.v_min + self.v_max) / 2.0)


class MonitorInfo(BaseModel):
    """Metadata describing a physical or virtual display monitor."""
    id: int
    name: str = "Display"
    x: int = 0
    y: int = 0
    width: int = 1920
    height: int = 1080
    scale_factor: float = 1.0
    is_primary: bool = True

    @property
    def bounds(self) -> BoundingBox:
        return BoundingBox(
            x=float(self.x),
            y=float(self.y),
            width=float(self.width),
            height=float(self.height),
            coordinate_space=CoordinateSpace.LOGICAL,
        )
