"""
SHIVANI UI Semantic Graph Engine (Phase 17).
Constructs a hierarchical functional graph of UI elements:
Window -> Sections (Toolbar, Sidebar, Content, Dialog, Status) -> Controls (Buttons, Inputs).
Enables semantic navigation such as 'Click Save in the Toolbar'.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field

from core.computer.models import ElementType, RectBounds, UIElement


class UIGraphNode(BaseModel):
    """A node in the semantic UI tree."""
    element: UIElement
    category: str = "Control"  # Root, Window, Toolbar, Sidebar, Content, Dialog, Control
    children: List[UIGraphNode] = Field(default_factory=list)

    @property
    def id(self) -> str:
        return self.element.id

    @property
    def text(self) -> str:
        return self.element.text

    @property
    def bounds(self) -> RectBounds:
        return self.element.bounds


class UISemanticGraph:
    """Manages the semantic hierarchy of UI components."""

    def __init__(self, elements: List[UIElement]):
        self.elements = elements
        self.nodes_by_id: Dict[str, UIGraphNode] = {}
        self.root: Optional[UIGraphNode] = None
        self._build_graph()

    def _classify_category(self, elem: UIElement) -> str:
        t = elem.type
        r = elem.role.lower()
        txt = elem.text.lower()

        if t == ElementType.WINDOW:
            return "Window"
        if t == ElementType.DIALOG or "dialog" in r:
            return "Dialog"
        if "toolbar" in r or "toolbar" in txt or "ribbon" in r:
            return "Toolbar"
        if "sidebar" in r or "explorer" in txt or "tree" in r:
            return "Sidebar"
        if "statusbar" in r or "status" in r:
            return "StatusBar"
        if t in (ElementType.BUTTON, ElementType.TEXT_FIELD, ElementType.CHECKBOX, ElementType.TAB):
            return "Control"
        return "Container"

    def _build_graph(self):
        # 1. Create nodes for all elements
        for elem in self.elements:
            cat = self._classify_category(elem)
            self.nodes_by_id[elem.id] = UIGraphNode(element=elem, category=cat)

        # 2. Wire up parent-child relationships
        orphans: List[UIGraphNode] = []
        for elem in self.elements:
            node = self.nodes_by_id[elem.id]
            if elem.parent_id and elem.parent_id in self.nodes_by_id:
                parent_node = self.nodes_by_id[elem.parent_id]
                parent_node.children.append(node)
            else:
                orphans.append(node)

        # 3. Create or attach to a virtual root
        root_elem = UIElement(
            id="ui_graph_root",
            type=ElementType.WINDOW,
            text="Desktop Root",
            bounds=RectBounds(left=0, top=0, width=3840, height=2160),
        )
        self.root = UIGraphNode(element=root_elem, category="Root", children=orphans)

    def find_in_section(self, section_name: str, control_text: str) -> Optional[UIElement]:
        """
        Finds a control matching control_text inside a container/section matching section_name.
        E.g. find_in_section("Toolbar", "Save")
        """
        sec_query = section_name.lower()
        ctrl_query = control_text.lower()

        # Search for matching section nodes
        target_sections: List[UIGraphNode] = []
        for node in self.nodes_by_id.values():
            if (
                sec_query in node.category.lower()
                or sec_query in node.text.lower()
                or sec_query in node.element.role.lower()
            ):
                target_sections.append(node)

        # In target sections, look for child matching control_text
        for sec in target_sections:
            for child in self._collect_descendants(sec):
                if ctrl_query in child.text.lower():
                    return child.element

        # If not found directly under container hierarchy, use spatial containment:
        for sec in target_sections:
            for elem in self.elements:
                if elem.id != sec.id and sec.bounds.contains(*elem.bounds.center):
                    if ctrl_query in elem.text.lower():
                        return elem

        return None

    def _collect_descendants(self, node: UIGraphNode) -> List[UIGraphNode]:
        result = []
        for child in node.children:
            result.append(child)
            result.extend(self._collect_descendants(child))
        return result

    def get_path_to_element(self, element_id: str) -> List[str]:
        """Returns the semantic path to an element, e.g. ['Window', 'Toolbar', 'Save']."""
        if element_id not in self.nodes_by_id:
            return []

        path = []
        curr: Optional[UIElement] = self.nodes_by_id[element_id].element
        while curr:
            name = curr.text or curr.type.value
            path.insert(0, name)
            if curr.parent_id and curr.parent_id in self.nodes_by_id:
                curr = self.nodes_by_id[curr.parent_id].element
            else:
                curr = None
        return path
