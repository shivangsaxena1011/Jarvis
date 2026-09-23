"""
SHIVANI Operating System Abstraction Layer
Defines clean contracts for OS-level window management, process lifecycle,
input synthesis, clipboard control, and screen capture.
Enables cross-platform extensibility (Windows 11 primary, Linux/macOS future).
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class WindowInfo(BaseModel):
    handle: int = Field(description="OS window handle or ID")
    title: str = Field(default="", description="Window title text")
    pid: Optional[int] = Field(default=None, description="Process ID associated with the window")
    app_name: Optional[str] = Field(default=None, description="Name of the application executable")
    rect: Dict[str, int] = Field(
        default_factory=lambda: {"left": 0, "top": 0, "width": 0, "height": 0},
        description="Window bounding box coordinates"
    )
    is_active: bool = Field(default=False, description="Whether window is currently focused")
    is_minimized: bool = Field(default=False, description="Whether window is minimized")
    is_maximized: bool = Field(default=False, description="Whether window is maximized")
    is_visible: bool = Field(default=True, description="Whether window is visible")


class OperatingSystemAdapter(ABC):
    """Abstract interface decoupling agent logic from OS-specific APIs."""

    @abstractmethod
    async def get_active_window(self) -> Optional[WindowInfo]:
        """Inspect and return the currently focused foreground window."""
        pass

    @abstractmethod
    async def list_windows(self, visible_only: bool = True) -> List[WindowInfo]:
        """Enumerate running windows with their handles and titles."""
        pass

    @abstractmethod
    async def find_windows_by_title(self, query: str, visible_only: bool = True) -> List[WindowInfo]:
        """Find open windows matching a substring or pattern."""
        pass

    @abstractmethod
    async def focus_window(self, identifier: Any) -> bool:
        """Bring window to foreground by handle, title, or WindowInfo."""
        pass

    @abstractmethod
    async def minimize_window(self, identifier: Any) -> bool:
        """Minimize window by handle or title."""
        pass

    @abstractmethod
    async def maximize_window(self, identifier: Any) -> bool:
        """Maximize window by handle or title."""
        pass

    @abstractmethod
    async def restore_window(self, identifier: Any) -> bool:
        """Restore window to normal state by handle or title."""
        pass

    @abstractmethod
    async def close_window(self, identifier: Any) -> bool:
        """Close window gracefully by sending close message."""
        pass

    @abstractmethod
    async def launch_app(self, executable: str, args: Optional[List[str]] = None) -> Dict[str, Any]:
        """Launch application process and return PID and initial status."""
        pass

    @abstractmethod
    async def resolve_app_path(self, app_name: str) -> Optional[str]:
        """Resolve executable path using registry, Start Menu, PATH, and known paths."""
        pass

    @abstractmethod
    async def list_installed_apps(self) -> List[Dict[str, str]]:
        """Discover installed applications on the host system."""
        pass

    @abstractmethod
    async def mouse_move(self, x: int, y: int, duration: float = 0.0) -> None:
        """Move cursor to coordinate (x, y)."""
        pass

    @abstractmethod
    async def mouse_click(
        self,
        button: str = "left",
        x: Optional[int] = None,
        y: Optional[int] = None,
        clicks: int = 1
    ) -> None:
        """Click mouse button at current or specified coordinate."""
        pass

    @abstractmethod
    async def mouse_drag(self, start_x: int, start_y: int, end_x: int, end_y: int, duration: float = 0.5) -> None:
        """Drag mouse from start coordinate to end coordinate."""
        pass

    @abstractmethod
    async def mouse_scroll(self, clicks: int) -> None:
        """Scroll vertical wheel (positive = up, negative = down)."""
        pass

    @abstractmethod
    async def get_cursor_position(self) -> Dict[str, int]:
        """Return current mouse cursor position {"x": x, "y": y}."""
        pass

    @abstractmethod
    async def keyboard_type(self, text: str, interval: float = 0.01) -> None:
        """Synthesize typing string into active focus."""
        pass

    @abstractmethod
    async def keyboard_press(self, key: str) -> None:
        """Press a single key (e.g. 'enter', 'tab', 'esc')."""
        pass

    @abstractmethod
    async def keyboard_hotkey(self, keys: List[str]) -> None:
        """Press key combination sequentially and release (e.g. ['ctrl', 'c'])."""
        pass

    @abstractmethod
    async def clipboard_read(self) -> str:
        """Read current textual contents of OS clipboard."""
        pass

    @abstractmethod
    async def clipboard_write(self, text: str) -> None:
        """Write string to OS clipboard."""
        pass

    @abstractmethod
    async def clipboard_clear(self) -> None:
        """Clear OS clipboard contents."""
        pass

    @abstractmethod
    async def capture_screen(
        self,
        output_path: Path,
        region: Optional[Dict[str, int]] = None,
        window_handle: Optional[int] = None
    ) -> Dict[str, Any]:
        """Capture screenshot of full screen, region, or specific window."""
        pass

    @abstractmethod
    async def get_screen_size(self) -> Dict[str, int]:
        """Return primary screen dimensions {"width": w, "height": h}."""
        pass
