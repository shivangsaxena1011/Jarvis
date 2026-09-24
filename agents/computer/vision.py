"""
SHIVANI Vision Provider Interface — Phase 10 Visual Computer Intelligence.
Establishes multimodal vision abstraction for UI element location,
screenshot description, and semantic perception.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from agents.computer.observation import DesktopElement
from vision.service import get_vision_service, VisionService


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


class Phase10VisionProvider(VisionProvider):
    """Production Phase 10 Vision Intelligence Provider backed by VisionService."""

    def __init__(self, vision_service: Optional[VisionService] = None):
        self.service = vision_service or get_vision_service()

    async def analyze_screenshot(self, screenshot_path: str) -> Dict[str, Any]:
        """Performs OCR and UI element detection on screenshot."""
        ocr_res = self.service.ocr_engine.extract(screenshot_path)
        ui_elems = self.service.element_detector.detect_elements(screenshot_path, ocr_res)

        desktop_elements: List[DesktopElement] = []
        for elem in ui_elems:
            desktop_elements.append(
                DesktopElement(
                    name=elem.text or elem.element_type.value,
                    element_type=elem.element_type.value,
                    confidence=elem.confidence,
                    bounding_box=elem.bounding_box.to_int_dict(),
                )
            )

        return {
            "screenshot": screenshot_path,
            "element_count": len(desktop_elements),
            "elements": [e.model_dump() for e in desktop_elements],
            "detected_text": [w.text for w in ocr_res.words],
            "full_text": ocr_res.full_text,
        }

    async def locate_element(self, screenshot_path: str, element_description: str) -> Optional[DesktopElement]:
        """Locates element via target grounding engine."""
        analysis = await self.analyze_screenshot(screenshot_path)
        # Check against detected elements
        desc_lower = element_description.lower()
        for elem_dict in analysis["elements"]:
            name_lower = elem_dict["name"].lower()
            if desc_lower in name_lower or name_lower in desc_lower:
                return DesktopElement(**elem_dict)
        return None

    async def describe_screen(self, screenshot_path: str) -> str:
        """Describes visual contents via VLM."""
        return await self.service.vlm.analyze_screen(screenshot_path, "Describe the active GUI elements on this screen.")


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
