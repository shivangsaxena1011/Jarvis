"""
SHIVANI Desktop Observation Engine (Phase 17).
Produces unified DesktopObservation snapshots by fusing OS Window state,
UI Automation accessibility trees, OCR detections, and Vision services.
"""

from __future__ import annotations
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from core.computer.models import (
    ApplicationContext,
    ApplicationState,
    DesktopObservation,
    ElementSource,
    ElementType,
    MonitorLayout,
    RectBounds,
    UIElement,
)
from core.computer.semantic_graph import UISemanticGraph
from core.computer.uia_engine import UIAEngine
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter


class ObservationEngine:
    """Coordinates desktop state capture across OS, UIA, Vision, and OCR."""

    def __init__(
        self,
        os_adapter: Optional[OperatingSystemAdapter] = None,
        uia_engine: Optional[UIAEngine] = None,
    ):
        self.os_adapter = os_adapter or get_os_adapter()
        self.uia_engine = uia_engine or UIAEngine()

    async def observe(
        self,
        capture_image: bool = True,
        synthetic_override: Optional[DesktopObservation] = None,
    ) -> DesktopObservation:
        """
        Gathers complete world state. If synthetic_override is provided,
        uses it (enabling deterministic testing).
        """
        if synthetic_override is not None:
            return synthetic_override

        timestamp = time.time()

        # 1. Active window & OS windows
        active_win = await self.os_adapter.get_active_window()
        active_title = active_win.title if active_win else ""
        active_pid = active_win.pid if active_win else None
        active_app = active_win.app_name if active_win else ""

        all_windows = await self.os_adapter.list_windows(visible_only=True)
        windows_data = [w.model_dump() for w in all_windows]

        # 2. Monitors
        monitors = [
            MonitorLayout(
                monitor_id=1,
                name="Primary Display",
                is_primary=True,
                width=1920,
                height=1080,
                scale_factor=1.0,
            )
        ]

        # 3. UIA Accessibility Elements
        elements: List[UIElement] = []
        if self.uia_engine.is_available() and active_title:
            uia_elements = self.uia_engine.inspect_active_window(window_title=active_title)
            elements.extend(uia_elements)

        # 4. Clipboard inspection with privacy masking
        clipboard_text: Optional[str] = None
        is_sensitive = False
        try:
            if hasattr(self.os_adapter, "clipboard_read"):
                raw_clip = await self.os_adapter.clipboard_read()
            elif hasattr(self.os_adapter, "clipboard_get"):
                raw_clip = await self.os_adapter.clipboard_get()
            else:
                raw_clip = None
            if raw_clip:
                # Check for sensitive tokens (passwords, JWTs, bearer tokens, private keys)
                if self._is_sensitive_text(raw_clip):
                    clipboard_text = "[REDACTED_SENSITIVE_CLIPBOARD]"
                    is_sensitive = True
                else:
                    clipboard_text = raw_clip[:500]  # truncate to prevent bloat
        except Exception:
            pass

        # 5. Application Context
        app_context = ApplicationContext(
            app_name=active_app or "Desktop",
            window_title=active_title,
            pid=active_pid,
            state=ApplicationState.READY,
        )

        return DesktopObservation(
            timestamp=timestamp,
            active_window=active_title,
            active_pid=active_pid,
            windows=windows_data,
            monitors=monitors,
            elements=elements,
            clipboard_text=clipboard_text,
            clipboard_is_sensitive=is_sensitive,
            application_context=app_context,
        )

    def _is_sensitive_text(self, text: str) -> bool:
        lower = text.lower()
        if any(w in lower for w in ["password", "bearer ", "eyj", "api_key", "secret", "private key"]):
            return True
        # Check for typical token hashes (e.g. 32+ hex or base64)
        if re.search(r"\b[A-Za-z0-9_-]{40,}\b", text):
            return True
        return False
