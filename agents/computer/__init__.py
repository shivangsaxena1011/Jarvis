from agents.computer.observation import DesktopObservation, ScreenGeometry, DesktopElement
from agents.computer.context import CurrentUIContext
from agents.computer.vision import VisionProvider, MockVisionProvider, Phase10VisionProvider
from agents.computer.observer import ScreenObserver
from agents.computer.browser_stub import BrowserAgent
from agents.computer.agent import ComputerAgent

__all__ = [
    "DesktopObservation",
    "ScreenGeometry",
    "DesktopElement",
    "CurrentUIContext",
    "VisionProvider",
    "MockVisionProvider",
    "Phase10VisionProvider",
    "ScreenObserver",
    "BrowserAgent",
    "ComputerAgent",
]
