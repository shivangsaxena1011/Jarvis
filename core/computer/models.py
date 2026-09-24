"""
SHIVANI Computer Autonomy & GUI Reasoning Data Models (Phase 17).
Defines comprehensive schemas for desktop observations, UI elements,
applications, closed-loop actions, expectations, checkpoints, and errors.
"""

from __future__ import annotations
from enum import Enum
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field


class ElementType(str, Enum):
    BUTTON = "BUTTON"
    TEXT_FIELD = "TEXT_FIELD"
    TEXT_AREA = "TEXT_AREA"
    CHECKBOX = "CHECKBOX"
    RADIO = "RADIO"
    DROPDOWN = "DROPDOWN"
    TAB = "TAB"
    MENU = "MENU"
    MENU_ITEM = "MENU_ITEM"
    LINK = "LINK"
    ICON = "ICON"
    IMAGE = "IMAGE"
    TABLE = "TABLE"
    ROW = "ROW"
    COLUMN = "COLUMN"
    CARD = "CARD"
    DIALOG = "DIALOG"
    WINDOW = "WINDOW"
    SLIDER = "SLIDER"
    TOGGLE = "TOGGLE"
    TREE = "TREE"
    LIST = "LIST"
    LIST_ITEM = "LIST_ITEM"
    SCROLLBAR = "SCROLLBAR"
    NOTIFICATION = "NOTIFICATION"
    UNKNOWN = "UNKNOWN"


class ElementSource(str, Enum):
    ACCESSIBILITY = "accessibility"
    DOM = "dom"
    APPLICATION_API = "application_api"
    OCR = "ocr"
    VISION = "vision"
    SPATIAL = "spatial"
    COORDINATE_FALLBACK = "coordinate_fallback"
    SYNTHETIC = "synthetic"


class ApplicationState(str, Enum):
    UNKNOWN = "UNKNOWN"
    LAUNCHING = "LAUNCHING"
    READY = "READY"
    BUSY = "BUSY"
    DIALOG_OPEN = "DIALOG_OPEN"
    ERROR = "ERROR"
    CLOSED = "CLOSED"
    CRASHED = "CRASHED"


class ActionType(str, Enum):
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE = "type"
    KEY_PRESS = "key_press"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    DRAG = "drag"
    DROP = "drop"
    SELECT = "select"
    FOCUS = "focus"
    COPY = "copy"
    PASTE = "paste"
    OPEN = "open"
    CLOSE = "close"
    MOVE_WINDOW = "move_window"
    RESIZE_WINDOW = "resize_window"
    SWITCH_WINDOW = "switch_window"
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class ErrorType(str, Enum):
    APPLICATION_ERROR = "APPLICATION_ERROR"
    NETWORK_ERROR = "NETWORK_ERROR"
    UI_CHANGED = "UI_CHANGED"
    ELEMENT_NOT_FOUND = "ELEMENT_NOT_FOUND"
    TIMEOUT = "TIMEOUT"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    INVALID_STATE = "INVALID_STATE"
    CRASH = "CRASH"
    LOOP_DETECTED = "LOOP_DETECTED"
    UNKNOWN = "UNKNOWN"


class CommandRisk(str, Enum):
    SAFE = "SAFE"
    SENSITIVE = "SENSITIVE"
    DANGEROUS = "DANGEROUS"
    PROHIBITED = "PROHIBITED"


class RectBounds(BaseModel):
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def center(self) -> Tuple[int, int]:
        return (self.left + self.width // 2, self.top + self.height // 2)

    def contains(self, x: int, y: int) -> bool:
        return self.left <= x <= self.right and self.top <= y <= self.bottom


class UIElement(BaseModel):
    """Rich structured model for any detected or inspected UI control."""
    id: str = Field(default_factory=lambda: f"elem_{uuid.uuid4().hex[:8]}")
    type: ElementType = ElementType.UNKNOWN
    text: str = ""
    role: str = ""
    bounds: RectBounds = Field(default_factory=RectBounds)
    enabled: bool = True
    visible: bool = True
    focused: bool = False
    selected: bool = False
    value: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: ElementSource = ElementSource.ACCESSIBILITY
    parent_id: Optional[str] = None
    children_ids: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class MonitorLayout(BaseModel):
    monitor_id: int = 1
    name: str = "Primary Monitor"
    is_primary: bool = True
    width: int = 1920
    height: int = 1080
    scale_factor: float = 1.0
    left: int = 0
    top: int = 0


class ApplicationContext(BaseModel):
    """Contextual metadata identifying the active software environment."""
    app_name: str = "Unknown"
    process_name: Optional[str] = None
    pid: Optional[int] = None
    window_title: str = ""
    window_handle: Optional[int] = None
    codebase_path: Optional[str] = None
    repo_url: Optional[str] = None
    state: ApplicationState = ApplicationState.READY
    is_elevated: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DesktopObservation(BaseModel):
    """Complete, unified snapshot of the desktop's world state."""
    timestamp: float = Field(default_factory=time.time)
    active_window: str = ""
    active_pid: Optional[int] = None
    windows: List[Dict[str, Any]] = Field(default_factory=list)
    monitors: List[MonitorLayout] = Field(default_factory=list)
    screenshot_path: Optional[str] = None
    accessibility_tree: Optional[Dict[str, Any]] = None
    ocr_results: List[Dict[str, Any]] = Field(default_factory=list)
    elements: List[UIElement] = Field(default_factory=list)
    cursor_position: Tuple[int, int] = (0, 0)
    clipboard_text: Optional[str] = None
    clipboard_is_sensitive: bool = False
    focused_element_id: Optional[str] = None
    application_context: ApplicationContext = Field(default_factory=ApplicationContext)
    browser_context: Optional[Dict[str, Any]] = None
    terminal_context: Optional[Dict[str, Any]] = None

    def find_elements_by_text(self, text: str, exact: bool = False) -> List[UIElement]:
        query = text.lower()
        results = []
        for elem in self.elements:
            elem_text = elem.text.lower()
            if exact and elem_text == query:
                results.append(elem)
            elif not exact and query in elem_text:
                results.append(elem)
        return results

    def find_element_by_id(self, elem_id: str) -> Optional[UIElement]:
        for elem in self.elements:
            if elem.id == elem_id:
                return elem
        return None


class ComputerAction(BaseModel):
    """Structured representation of a single atomic or composite computer action."""
    id: str = Field(default_factory=lambda: f"act_{uuid.uuid4().hex[:8]}")
    action_type: ActionType
    target: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    expected_state: Dict[str, Any] = Field(default_factory=dict)
    risk: str = "LOW"
    confidence: float = 1.0
    timeout_seconds: float = 10.0
    verification: Dict[str, Any] = Field(default_factory=dict)
    rollback: Optional[Dict[str, Any]] = None


class StateDifference(BaseModel):
    """Detected delta between pre-action and post-action world states."""
    active_window_changed: bool = False
    new_window_title: Optional[str] = None
    new_dialog_detected: bool = False
    dialog_type: Optional[str] = None
    text_changed: bool = False
    added_text: List[str] = Field(default_factory=list)
    removed_text: List[str] = Field(default_factory=list)
    elements_added: int = 0
    elements_removed: int = 0
    files_created: List[str] = Field(default_factory=list)
    process_started: Optional[str] = None
    error_detected: bool = False
    error_message: Optional[str] = None
    screenshot_diff_ratio: float = 0.0


class ActionExecutionResult(BaseModel):
    """Complete result record for an executed action."""
    action_id: str
    action_type: ActionType
    success: bool
    verified: bool
    state_diff: StateDifference = Field(default_factory=StateDifference)
    duration_seconds: float = 0.0
    confidence: float = 1.0
    failure_reason: Optional[str] = None
    error_type: Optional[ErrorType] = None
    observation_after: Optional[DesktopObservation] = None


class TaskCheckpoint(BaseModel):
    """Persistent recovery checkpoint for a long-horizon computer workflow."""
    checkpoint_id: str = Field(default_factory=lambda: f"ckpt_{uuid.uuid4().hex[:8]}")
    task_id: str
    step_index: int
    timestamp: float = Field(default_factory=time.time)
    app_context: ApplicationContext
    completed_actions: List[Dict[str, Any]] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    pending_steps: List[str] = Field(default_factory=list)
    summary: str = ""
