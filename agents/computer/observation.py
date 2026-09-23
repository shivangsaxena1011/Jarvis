"""
SHIVANI Desktop Observation
Defines structured desktop observation representation returned by ScreenObserver.
Ready for multimodal vision and UI accessibility tree ingestion.
"""

import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScreenGeometry(BaseModel):
    width: int = Field(default=1920, description="Screen width in pixels")
    height: int = Field(default=1080, description="Screen height in pixels")


class DesktopElement(BaseModel):
    name: str = Field(description="Element semantic name or label (e.g. 'Search Bar', 'Submit Button')")
    element_type: str = Field(default="unknown", description="Type of UI control (e.g. button, input, text, window)")
    confidence: float = Field(default=1.0, description="Detection confidence score (0.0 - 1.0)")
    bounding_box: Dict[str, int] = Field(
        default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0},
        description="Bounding box coordinates in pixels"
    )


class DesktopObservation(BaseModel):
    screen: ScreenGeometry = Field(default_factory=ScreenGeometry)
    active_window: str = Field(default="Unknown", description="Title of currently focused window")
    active_pid: Optional[int] = Field(default=None, description="PID of currently focused window")
    active_app: Optional[str] = Field(default=None, description="Application executable of focused window")
    elements: List[DesktopElement] = Field(default_factory=list, description="Detected visual or accessibility UI elements")
    screenshot_path: Optional[str] = Field(default=None, description="Path to captured screenshot image")
    timestamp: float = Field(default_factory=time.time, description="Observation timestamp in seconds")
