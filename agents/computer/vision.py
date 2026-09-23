"""
SHIVANI Vision Provider Interface
Establishes multimodal vision abstraction for UI element location,
screenshot description, and semantic perception.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from agents.computer.observation import DesktopElement


class VisionProvider(ABC):
    """Abstract interface for screenshot analysis and UI element detection."""

    @abstractmethod
    async def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """Performs full vision pass over screenshot returning detected regions and text."""
        pass

    @abstractmethod
    async def locate_element(self, screenshot_path: str, element_description: str) -> Optional[DesktopElement]:
        """Locates specific semantic UI element in screenshot and returns bounding box."""
        pass

    @abstractmethod
    async def describe_screen(self, screenshot_path: str) -> str:
        """Generates natural language summary of the screen state."""
        pass


class MockVisionProvider(VisionProvider):
    """Deterministic local mock vision provider for zero-cost offline execution."""

    def __init__(self, elements: Optional[List[DesktopElement]] = None):
        self.preset_elements = elements or [
            DesktopElement(
                name="Search box",
                element_type="input",
                confidence=0.96,
                bounding_box={"x": 400, "y": 120, "width": 500, "height": 60}
            ),
            DesktopElement(
                name="Submit button",
                element_type="button",
                confidence=0.94,
                bounding_box={"x": 920, "y": 120, "width": 100, "height": 60}
            ),
            DesktopElement(
                name="Close window",
                element_type="button",
                confidence=0.98,
                bounding_box={"x": 1880, "y": 10, "width": 30, "height": 30}
            ),
        ]

    async def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        return {
            "screenshot": screenshot_path,
            "element_count": len(self.preset_elements),
            "elements": [e.model_dump() for e in self.preset_elements],
            "detected_text": ["Search", "Submit", "Settings"]
        }

    async def locate_element(self, screenshot_path: str, element_description: str) -> Optional[DesktopElement]:
        desc_lower = element_description.lower()
        for elem in self.preset_elements:
            if desc_lower in elem.name.lower() or elem.name.lower() in desc_lower:
                return elem
        return None

    async def describe_screen(self, screenshot_path: str) -> str:
        return "Desktop screen with application window open, containing search box and controls."
