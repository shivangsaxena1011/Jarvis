"""
SHIVANI Visual UI Tree Builder.
Organizes flat detected elements into a hierarchical spatial containment tree.
"""

from __future__ import annotations
from typing import List, Optional
from vision.models.types import (
    BoundingBox,
    CoordinateSpace,
    VisualElementType,
)
from vision.models.schemas import UIElement, UITreeNode
from vision.ocr.fuzzy import fuzzy_match_ratio


class VisualUITreeBuilder:
    """Constructs a spatial containment tree from a list of UI elements."""

    def build_tree(
        self,
        elements: List[UIElement],
        root_bounds: Optional[BoundingBox] = None,
    ) -> UITreeNode:
        """
        Builds a hierarchical tree where containers parent their enclosed elements.
        """
        if root_bounds is None:
            root_bounds = BoundingBox(
                x=0.0,
                y=0.0,
                width=1920.0,
                height=1080.0,
                coordinate_space=CoordinateSpace.LOGICAL,
            )

        root_element = UIElement(
            id="root_screen",
            element_type=VisualElementType.CONTAINER,
            bounding_box=root_bounds,
            text="Screen Root",
            confidence=1.0,
        )
        root_node = UITreeNode(element=root_element, depth=0)

        # Sort elements by area descending so containers are processed before children
        sorted_elements = sorted(
            elements,
            key=lambda e: e.bounding_box.area,
            reverse=True,
        )

        nodes: List[UITreeNode] = [UITreeNode(element=e) for e in sorted_elements]

        # Insert each node into the tightest enclosing container
        for node in nodes:
            self._insert_into_tree(root_node, node)

        return root_node

    def _insert_into_tree(self, parent: UITreeNode, child: UITreeNode) -> bool:
        """Attempts to insert child into the deepest enclosing sub-tree."""
        # First check if any existing child of parent can enclose this node
        for existing_child in parent.children:
            if existing_child.element.bounding_box.contains_box(child.element.bounding_box):
                return self._insert_into_tree(existing_child, child)

        # If no child encloses it, parent takes ownership
        child.depth = parent.depth + 1
        child.element.parent_id = parent.element.id
        parent.element.children_ids.append(child.element.id)
        parent.children.append(child)
        return True


class VisualUITreeQuery:
    """Helper for querying a built Visual UI Tree."""

    def __init__(self, root: UITreeNode):
        self.root = root

    def find_by_text(
        self,
        query: str,
        fuzzy: bool = True,
        threshold: float = 0.7,
    ) -> List[UIElement]:
        """Finds elements matching the text query."""
        results: List[UIElement] = []
        q_norm = query.strip().lower()

        def _traverse(node: UITreeNode):
            if node.element.text:
                t_norm = node.element.text.strip().lower()
                if fuzzy:
                    if fuzzy_match_ratio(q_norm, t_norm) >= threshold:
                        results.append(node.element)
                else:
                    if q_norm in t_norm:
                        results.append(node.element)
            for c in node.children:
                _traverse(c)

        _traverse(self.root)
        return results

    def find_by_type(self, elem_type: VisualElementType) -> List[UIElement]:
        """Finds all elements matching an element type."""
        return self.root.find_all_by_type(elem_type)

    def get_all_elements(self) -> List[UIElement]:
        """Flattens the tree into a list of all elements."""
        elems: List[UIElement] = []

        def _traverse(node: UITreeNode):
            if node.element.id != "root_screen":
                elems.append(node.element)
            for c in node.children:
                _traverse(c)

        _traverse(self.root)
        return elems
