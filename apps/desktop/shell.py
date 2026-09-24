"""
SHIVANI Desktop Shell Controller
Orchestrates multi-surface desktop presentation modes:
- Dashboard: Full comprehensive assistant workstation
- Floating HUD: Compact, draggable, state-reactive desktop widget
- Command Bar: Spotlight-style quick keyboard prompt
- System Tray: Headless background assistant with quick actions
"""

from enum import Enum
import logging
import os
import subprocess
import webbrowser
from typing import Any, Dict, Optional

from apps.desktop.tray import SystemTrayManager, TrayStatus

logger = logging.getLogger("shivani.desktop.shell")


class ShellMode(str, Enum):
    DASHBOARD = "dashboard"
    HUD = "hud"
    COMMAND_BAR = "command"
    TRAY = "tray"


class DesktopShell:
    """Coordinates desktop UI modes, tray events, and hotkey actions."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.mode: ShellMode = ShellMode.DASHBOARD
        self.base_url = f"http://{host}:{port}"
        self.tray = SystemTrayManager(
            on_open_dashboard=lambda: self.switch_mode(ShellMode.DASHBOARD),
            on_open_hud=lambda: self.switch_mode(ShellMode.HUD),
            on_open_command=lambda: self.switch_mode(ShellMode.COMMAND_BAR),
            on_emergency_stop=self.trigger_emergency_stop,
            on_toggle_privacy=self.toggle_privacy_mode,
            on_toggle_lock=self.toggle_lock,
            on_quit=self.shutdown,
        )

    def start(self, mode: ShellMode = ShellMode.DASHBOARD) -> None:
        """Starts desktop shell in the designated mode."""
        self.mode = mode
        self.tray.start()
        if mode != ShellMode.TRAY:
            self.open_ui(mode)
        logger.info(f"Desktop Shell initialized in {mode.value} mode at {self.base_url}")

    def switch_mode(self, new_mode: ShellMode) -> None:
        """Transitions desktop shell to another mode."""
        self.mode = new_mode
        self.open_ui(new_mode)
        logger.info(f"Switched Desktop Shell mode to: {new_mode.value}")

    def open_ui(self, mode: Optional[ShellMode] = None) -> None:
        """Opens or focuses browser interface in specified mode."""
        target_mode = (mode or self.mode).value
        url = f"{self.base_url}/?mode={target_mode}"
        try:
            webbrowser.open(url)
        except Exception as e:
            logger.warning(f"Could not open browser for URL {url}: {e}")

    def trigger_emergency_stop(self) -> None:
        logger.warning("Emergency Stop invoked from Desktop Shell.")
        try:
            import httpx
            httpx.post(f"{self.base_url}/api/stop", timeout=2.0)
        except Exception:
            pass

    def toggle_privacy_mode(self) -> bool:
        try:
            import httpx
            res = httpx.post(f"{self.base_url}/api/state/control", json={"action": "privacy_toggle"}, timeout=2.0)
            data = res.json()
            is_on = data.get("privacy_mode", False)
            self.tray.privacy_mode = is_on
            self.tray._update_tooltip()
            return is_on
        except Exception:
            return False

    def toggle_lock(self) -> bool:
        try:
            import httpx
            res = httpx.post(f"{self.base_url}/api/state/control", json={"action": "lock"}, timeout=2.0)
            self.tray.locked = True
            self.tray.set_status(TrayStatus.LOCKED)
            return True
        except Exception:
            return False

    def update_tray_status(self, status: TrayStatus) -> None:
        self.tray.set_status(status)

    def shutdown(self) -> None:
        logger.info("Shutting down Desktop Shell.")
        self.tray.stop()
