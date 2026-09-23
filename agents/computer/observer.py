"""
SHIVANI Screen Observer
Captures desktop state, queries active window and screen dimensions,
and delegates to VisionProvider or UI accessibility providers to generate
structured DesktopObservation objects.
"""

from typing import Any, Dict, Optional
from agents.computer.observation import DesktopObservation, ScreenGeometry, DesktopElement
from agents.computer.vision import VisionProvider, MockVisionProvider
from tools.desktop.screen import ScreenCapture
from tools.desktop.window import WindowManager


class ScreenObserver:
    """Produces structured multi-attribute desktop observations."""

    def __init__(
        self,
        screen_capture: Optional[ScreenCapture] = None,
        window_manager: Optional[WindowManager] = None,
        vision_provider: Optional[VisionProvider] = None
    ):
        self.screen_capture = screen_capture or ScreenCapture()
        self.window_manager = window_manager or WindowManager()
        self.vision = vision_provider or MockVisionProvider()

    async def observe(self, capture_image: bool = True) -> DesktopObservation:
        """
        Executes a screen observation pass.
        Captures screenshot, active window information, and detects elements.
        """
        active_win = await self.window_manager.get_active_window()
        active_title = active_win.title if active_win else "Unknown"
        active_pid = active_win.pid if active_win else None
        active_app = active_win.app_name if active_win else None

        screenshot_path = None
        width = 1920
        height = 1080

        if capture_image:
            capture_res = await self.screen_capture.capture()
            screenshot_path = capture_res.get("path")
            width = capture_res.get("width", 1920)
            height = capture_res.get("height", 1080)

        # Query vision provider if screenshot is available
        detected_elements = []
        if screenshot_path and self.vision:
            try:
                analysis = await self.vision.analyze_screenshot(screenshot_path)
                for elem_data in analysis.get("elements", []):
                    detected_elements.append(DesktopElement(**elem_data))
            except Exception:
                pass

        return DesktopObservation(
            screen=ScreenGeometry(width=width, height=height),
            active_window=active_title,
            active_pid=active_pid,
            active_app=active_app,
            elements=detected_elements,
            screenshot_path=screenshot_path
        )
