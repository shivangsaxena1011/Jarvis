"""
SHIVANI Windows UI Automation Engine (Phase 17).
Provides accessibility tree inspection, control pattern invocation,
and semantic UI control extraction using Win32 / pywinauto / comtypes.
"""

from __future__ import annotations
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from core.computer.models import ElementSource, ElementType, RectBounds, UIElement

logger = logging.getLogger("shivani.computer.uia")

# Control type mapping from Win32 / UIA strings to ElementType
UIA_TYPE_MAP = {
    "Button": ElementType.BUTTON,
    "SplitButton": ElementType.BUTTON,
    "Edit": ElementType.TEXT_FIELD,
    "Document": ElementType.TEXT_AREA,
    "CheckBox": ElementType.CHECKBOX,
    "RadioButton": ElementType.RADIO,
    "ComboBox": ElementType.DROPDOWN,
    "Tab": ElementType.TAB,
    "TabItem": ElementType.TAB,
    "Menu": ElementType.MENU,
    "MenuBar": ElementType.MENU,
    "MenuItem": ElementType.MENU_ITEM,
    "Hyperlink": ElementType.LINK,
    "Image": ElementType.IMAGE,
    "Table": ElementType.TABLE,
    "DataGrid": ElementType.TABLE,
    "DataItem": ElementType.ROW,
    "Header": ElementType.ROW,
    "HeaderItem": ElementType.COLUMN,
    "Window": ElementType.WINDOW,
    "Dialog": ElementType.DIALOG,
    "Slider": ElementType.SLIDER,
    "ProgressBar": ElementType.SLIDER,
    "Tree": ElementType.TREE,
    "TreeItem": ElementType.LIST_ITEM,
    "List": ElementType.LIST,
    "ListItem": ElementType.LIST_ITEM,
    "ScrollBar": ElementType.SCROLLBAR,
    "ToolTip": ElementType.NOTIFICATION,
    "Text": ElementType.CARD,
    "Pane": ElementType.CARD,
    "Group": ElementType.CARD,
}


class UIAEngine:
    """Windows UI Automation coordinator with robust fallback."""

    def __init__(self, backend: str = "uia"):
        self.backend = backend
        self._uia_available = False
        try:
            import pywinauto
            from pywinauto import Desktop
            self._Desktop = Desktop
            self._uia_available = True
        except Exception as e:
            logger.debug(f"pywinauto UIAutomation not active or unavailable: {e}")
            self._Desktop = None

    def is_available(self) -> bool:
        return self._uia_available and self._Desktop is not None

    def inspect_active_window(
        self, window_title: Optional[str] = None, max_depth: int = 4
    ) -> List[UIElement]:
        """
        Extracts all accessible UI controls from the foreground or targeted window.
        """
        if not self.is_available():
            return []

        elements: List[UIElement] = []
        try:
            desktop = self._Desktop(backend=self.backend)
            if window_title:
                win = desktop.window(title_re=f".*{window_title}.*")
            else:
                win = desktop.windows(visible_only=True)[0]

            def walk_wrapper(ctrl: Any, parent_id: Optional[str] = None, depth: int = 0):
                if depth > max_depth:
                    return
                try:
                    rect = ctrl.rectangle()
                    ctrl_type = ctrl.element_info.control_type or "Unknown"
                    elem_type = UIA_TYPE_MAP.get(ctrl_type, ElementType.UNKNOWN)
                    name = ctrl.element_info.name or ""
                    
                    bounds = RectBounds(
                        left=rect.left,
                        top=rect.top,
                        width=max(0, rect.width()),
                        height=max(0, rect.height()),
                    )

                    elem = UIElement(
                        type=elem_type,
                        text=name,
                        role=ctrl_type,
                        bounds=bounds,
                        enabled=ctrl.is_enabled(),
                        visible=ctrl.is_visible(),
                        source=ElementSource.ACCESSIBILITY,
                        parent_id=parent_id,
                        confidence=0.98,
                    )
                    elements.append(elem)

                    for child in ctrl.children():
                        walk_wrapper(child, parent_id=elem.id, depth=depth + 1)
                except Exception:
                    pass

            walk_wrapper(win)
        except Exception as e:
            logger.debug(f"UIA inspection encountered an issue: {e}")

        return elements

    def invoke_control(self, window_title: str, control_name: str) -> bool:
        """
        Attempts to invoke or click a named control directly via UIA pattern.
        """
        if not self.is_available():
            return False

        try:
            desktop = self._Desktop(backend=self.backend)
            win = desktop.window(title_re=f".*{window_title}.*")
            btn = win.child_window(title=control_name)
            if btn.exists():
                btn.click_input()
                return True
        except Exception as e:
            logger.debug(f"Direct UIA invocation failed: {e}")
        return False
