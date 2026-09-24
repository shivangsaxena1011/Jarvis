"""
SHIVANI Vision Schemas — Hierarchical UI Elements, OCR Results & Visual Context.
"""

from __future__ import annotations
import uuid
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    MonitorInfo,
    VisualElementType,
    VisualState,
)


class UIElement(BaseModel):
    """Semantic representation of an interactable or informative GUI element."""
    id: str = Field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")
    element_type: VisualElementType = VisualElementType.UNKNOWN
    bounding_box: BoundingBox
    text: Optional[str] = None
    confidence: float = 1.0
    state: VisualState = VisualState.NORMAL
    attributes: Dict[str, Any] = Field(default_factory=dict)
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)

    @property
    def center_click_point(self) -> Dict[str, float]:
        """Returns the logical center coordinates to target for mouse interactions."""
        center = self.bounding_box.center
        return {"x": center.x, "y": center.y}


class UITreeNode(BaseModel):
    """Hierarchical node in a visual containment tree."""
    element: UIElement
    children: List[UITreeNode] = Field(default_factory=list)
    depth: int = 0

    def find_by_id(self, elem_id: str) -> Optional[UIElement]:
        if self.element.id == elem_id:
            return self.element
        for child in self.children:
            found = child.find_by_id(elem_id)
            if found:
                return found
        return None

    def find_all_by_type(self, elem_type: VisualElementType) -> List[UIElement]:
        results: List[UIElement] = []
        if self.element.element_type == elem_type:
            results.append(self.element)
        for child in self.children:
            results.extend(child.find_all_by_type(elem_type))
        return results


class OCRWord(BaseModel):
    """Individual recognized word with spatial bounds."""
    text: str
    bounding_box: BoundingBox
    confidence: float = 1.0
    script: str = "latin"  # 'latin', 'devanagari', etc.


class OCRLine(BaseModel):
    """Horizontal line of recognized words."""
    text: str
    bounding_box: BoundingBox
    words: List[OCRWord] = Field(default_factory=list)
    confidence: float = 1.0


class OCRBlock(BaseModel):
    """Multi-line textual paragraph or UI label block."""
    text: str
    bounding_box: BoundingBox
    lines: List[OCRLine] = Field(default_factory=list)
    block_type: str = "paragraph"  # 'paragraph', 'header', 'label', 'button_text'
    confidence: float = 1.0


class OCRResult(BaseModel):
    """Comprehensive structured output of an OCR extraction pass."""
    full_text: str = ""
    blocks: List[OCRBlock] = Field(default_factory=list)
    lines: List[OCRLine] = Field(default_factory=list)
    words: List[OCRWord] = Field(default_factory=list)
    language: str = "en"
    execution_time_ms: float = 0.0

    def find_text(self, query: str, case_sensitive: bool = False) -> List[OCRWord]:
        """Finds all word tokens matching a query string."""
        q = query if case_sensitive else query.lower()
        matches = []
        for word in self.words:
            w = word.text if case_sensitive else word.text.lower()
            if q in w:
                matches.append(word)
        return matches


class VisualDelta(BaseModel):
    """Differential analysis between two sequential screen states."""
    has_changed: bool = False
    change_percentage: float = 0.0
    changed_region: Optional[BoundingBox] = None
    newly_appeared_elements: List[UIElement] = Field(default_factory=list)
    disappeared_elements: List[UIElement] = Field(default_factory=list)
    description: str = "No noticeable screen difference."


class VisualContext(BaseModel):
    """Unified multi-modal state snapshot representing the user's screen."""
    screenshot_path: str
    timestamp: float
    monitor: MonitorInfo
    active_window: Dict[str, Any] = Field(default_factory=dict)
    ocr: Optional[OCRResult] = None
    elements: List[UIElement] = Field(default_factory=list)
    ui_tree: Optional[UITreeNode] = None
    accessibility_nodes: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
