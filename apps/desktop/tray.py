"""
SHIVANI Windows System Tray Integration
Native Windows System Tray (Taskbar Notification Area) icon and menu manager
using win32gui and Shell_NotifyIcon.
Supports dynamic state badges: Ready, Listening, Processing, Speaking,
Working, Waiting for approval, Paused, Offline, Error, Locked.
"""

from enum import Enum
import logging
import os
import sys
import threading
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("shivani.desktop.tray")


class TrayStatus(str, Enum):
    READY = "Ready"
    LISTENING = "Listening..."
    PROCESSING = "Processing..."
    SPEAKING = "Speaking..."
    WORKING = "Working on task..."
    WAITING_APPROVAL = "Waiting for approval"
    PAUSED = "Paused"
    OFFLINE = "Offline"
    ERROR = "Error"
    LOCKED = "Locked"


class SystemTrayManager:
    """Manages system tray icon, dynamic status tooltip, and context menu."""

    def __init__(
        self,
        on_open_dashboard: Optional[Callable[[], None]] = None,
        on_open_hud: Optional[Callable[[], None]] = None,
        on_open_command: Optional[Callable[[], None]] = None,
        on_emergency_stop: Optional[Callable[[], None]] = None,
        on_toggle_privacy: Optional[Callable[[], None]] = None,
        on_toggle_lock: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ):
        self.status = TrayStatus.READY
        self.privacy_mode = False
        self.locked = False
        self.is_running = False

        self.on_open_dashboard = on_open_dashboard
        self.on_open_hud = on_open_hud
        self.on_open_command = on_open_command
        self.on_emergency_stop = on_emergency_stop
        self.on_toggle_privacy = on_toggle_privacy
        self.on_toggle_lock = on_toggle_lock
        self.on_quit = on_quit

        self._hwnd = None
        self._thread: Optional[threading.Thread] = None

    def set_status(self, status: TrayStatus) -> None:
        """Dynamically updates tray tooltip and state badge."""
        self.status = status
        self._update_tooltip()
        logger.info(f"Tray status updated to: {status.value}")

    def get_status_summary(self) -> Dict[str, Any]:
        return {
            "status": self.status.value,
            "privacy_mode": self.privacy_mode,
            "locked": self.locked,
            "is_running": self.is_running,
        }

    def _update_tooltip(self) -> None:
        tooltip = f"SHIVANI — {self.status.value}"
        if self.privacy_mode:
            tooltip += " [PRIVACY ON]"
        if self.locked:
            tooltip += " [LOCKED]"

        if os.name == "nt" and self._hwnd:
            try:
                import win32gui
                nid = (self._hwnd, 0, win32gui.NIF_TIP, 0, 0, tooltip)
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
            except Exception as e:
                logger.debug(f"Tray tooltip update error: {e}")

    def start(self) -> None:
        """Starts tray manager loop."""
        self.is_running = True
        if os.name == "nt":
            self._thread = threading.Thread(target=self._run_win32_loop, daemon=True)
            self._thread.start()
        logger.info("System Tray Manager started.")

    def stop(self) -> None:
        """Removes icon and terminates tray thread."""
        self.is_running = False
        if os.name == "nt" and self._hwnd:
            try:
                import win32gui
                win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
            except Exception:
                pass
        logger.info("System Tray Manager stopped.")

    def _run_win32_loop(self) -> None:
        try:
            import win32gui
            import win32con

            # Register hidden message window class for tray callbacks
            wc = win32gui.WNDCLASS()
            hinst = wc.hInstance = win32gui.GetModuleHandle(None)
            wc.lpszClassName = "ShivaniTrayMsgWindow"
            wc.lpfnWndProc = self._wnd_proc

            class_atom = win32gui.RegisterClass(wc)
            self._hwnd = win32gui.CreateWindow(
                class_atom, "ShivaniTrayMsgWindow", 0, 0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None
            )

            # Standard icon
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
            nid = (
                self._hwnd,
                0,
                win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                win32con.WM_USER + 20,
                hicon,
                f"SHIVANI — {self.status.value}",
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)

            # Message pump
            win32gui.PumpMessages()
        except Exception as e:
            logger.warning(f"Win32 tray loop non-fatal warning: {e}")

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        import win32con
        if msg == win32con.WM_USER + 20:
            # lparam contains mouse events
            if lparam == win32con.WM_LBUTTONUP:
                if self.on_open_dashboard:
                    self.on_open_dashboard()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu(hwnd)
        return 0

    def _show_menu(self, hwnd):
        try:
            import win32gui
            import win32con

            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING | win32con.MF_GRAYED, 100, f"SHIVANI ({self.status.value})")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1, "Ask Shivani (Command Bar)")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 2, "Open Assistant Dashboard")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 3, "Floating HUD Mode")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 4, "Toggle Privacy Mode")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 5, "Lock Shivani")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 6, "Emergency Stop Task")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 9, "Quit Shivani")

            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(hwnd)
            cmd = win32gui.TrackPopupMenu(menu, win32con.TPM_RETURNCMD, pos[0], pos[1], 0, hwnd, None)
            win32gui.DestroyMenu(menu)

            if cmd == 1 and self.on_open_command:
                self.on_open_command()
            elif cmd == 2 and self.on_open_dashboard:
                self.on_open_dashboard()
            elif cmd == 3 and self.on_open_hud:
                self.on_open_hud()
            elif cmd == 4 and self.on_toggle_privacy:
                self.on_toggle_privacy()
            elif cmd == 5 and self.on_toggle_lock:
                self.on_toggle_lock()
            elif cmd == 6 and self.on_emergency_stop:
                self.on_emergency_stop()
            elif cmd == 9 and self.on_quit:
                self.on_quit()
        except Exception as e:
            logger.debug(f"Tray menu display error: {e}")
