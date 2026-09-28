"""
SHIVANI Computer Agent
Autonomous coordinator for desktop operations.
Manages screen observations, UI context, application/window lifecycle,
safe input dispatch, and failure recovery.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional

from agents.computer.observation import DesktopObservation
from agents.computer.context import CurrentUIContext
from agents.computer.observer import ScreenObserver
from agents.computer.vision import VisionProvider
from agents.computer.browser_stub import BrowserAgent
from tools.desktop.application import ApplicationManager
from tools.desktop.window import WindowManager
from tools.desktop.input import InputController
from tools.desktop.screen import ScreenCapture
from tools.desktop.clipboard import ClipboardManager
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter
from core.config import get_settings
from core.computer.agent import ComputerAutonomyAgent


class ComputerAgent:
    """High-level autonomous computer-use agent for desktop control."""

    def __init__(
        self,
        adapter: Optional[OperatingSystemAdapter] = None,
        context: Optional[CurrentUIContext] = None,
        vision_provider: Optional[VisionProvider] = None
    ):
        self.adapter = adapter or get_os_adapter()
        self.context = context or CurrentUIContext()
        self.settings = get_settings()

        self.apps = ApplicationManager(self.adapter)
        self.windows = WindowManager(self.adapter)
        self.input = InputController(self.adapter)
        self.screen = ScreenCapture(self.adapter)
        self.clipboard = ClipboardManager(self.adapter)
        self.observer = ScreenObserver(screen_capture=self.screen, window_manager=self.windows, vision_provider=vision_provider)
        self.browser = BrowserAgent(self.adapter)
        self.autonomy = ComputerAutonomyAgent(os_adapter=self.adapter)

    async def observe(self, capture_image: bool = True) -> DesktopObservation:
        """Observes the current desktop environment and updates UI context."""
        obs = await self.observer.observe(capture_image=capture_image)
        self.context.update_active_window(
            title=obs.active_window,
            app_name=obs.active_app,
            pid=obs.active_pid
        )
        if obs.screenshot_path:
            self.context.set_last_screenshot(obs.screenshot_path)
        return obs

    async def open_app(self, app_name: str, arguments: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launches application and updates UI context upon verification."""
        res = await self.apps.open_application(app_name, arguments=arguments)
        await self.observe(capture_image=False)
        return res

    async def close_app(self, app_name: Optional[str] = None, pid: Optional[int] = None) -> Dict[str, Any]:
        """Closes application and refreshes desktop observation."""
        res = await self.apps.close_application(app_name=app_name, pid=pid)
        await self.observe(capture_image=False)
        return res

    async def focus_window(self, target: str) -> Dict[str, Any]:
        """Brings target window into foreground."""
        res = await self.windows.focus_window(target)
        if res.get("verified"):
            self.context.update_active_window(title=res.get("active_window_title"))
        return res

    async def minimize_window(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Minimizes specified or active window."""
        effective_target = target or self.context.active_window
        return await self.windows.minimize_window(effective_target)

    async def maximize_window(self, target: Optional[str] = None) -> Dict[str, Any]:
        """Maximizes specified or active window."""
        effective_target = target or self.context.active_window
        return await self.windows.maximize_window(effective_target)

    async def safe_type(self, text: str, target_window: Optional[str] = None) -> Dict[str, Any]:
        """Types text with focus check safety."""
        return await self.input.type_text(text, target_window=target_window)

    async def safe_click(
        self,
        x: Optional[int] = None,
        y: Optional[int] = None,
        button: str = "left",
        target_window: Optional[str] = None
    ) -> Dict[str, Any]:
        """Clicks at target coordinates with focus check safety."""
        return await self.input.click(button=button, x=x, y=y, target_window=target_window)

    async def click_element_by_vision(self, query: str) -> Dict[str, Any]:
        """Grounds target query visually and performs safe click."""
        from vision.service import get_vision_service
        service = get_vision_service()
        elem, point, conf = service.locate_target(query)
        if not elem or not point:
            return {"success": False, "details": f"Could not visually ground target '{query}'."}
        pt = point.as_int_tuple()
        click_res = await self.safe_click(x=pt[0], y=pt[1])
        return {
            "success": True,
            "element": elem.id,
            "text": elem.text,
            "confidence": conf,
            "click_result": click_res,
        }

    async def execute_with_recovery(
        self,
        action_fn: Callable[..., Any],
        *args: Any,
        max_retries: Optional[int] = None,
        action_name: str = "computer_action",
        **kwargs: Any
    ) -> Any:
        """
        Executes action with exponential backoff retries and screenshot capture on failure.
        """
        retries = max_retries or self.settings.DESKTOP_MAX_RETRIES
        last_error = None

        for attempt in range(1, retries + 1):
            try:
                return await action_fn(*args, **kwargs)
            except Exception as e:
                last_error = str(e)
                # On failure, capture failure screenshot for diagnostic feedback
                try:
                    fail_shot = await self.screen.capture(filename=f"failure_{action_name}_{attempt}.png")
                    self.context.set_last_screenshot(fail_shot.get("path", ""))
                except Exception:
                    pass

                if attempt < retries:
                    backoff = 0.5 * (2 ** (attempt - 1))
                    await asyncio.sleep(backoff)

        raise RuntimeError(f"Action '{action_name}' failed after {retries} attempts: {last_error}")
