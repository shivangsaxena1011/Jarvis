"""
SHIVANI Desktop Browser Application Adapter (Phase 17).
Provides keyboard shortcuts and address-bar control for Chrome and Edge,
facilitating seamless handoff between Playwright DOM and GUI interactions.
"""

from __future__ import annotations
from typing import Any, Dict, List
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class BrowserAdapter(ApplicationAdapter):
    """Specialized adapter for Chrome and Microsoft Edge."""

    @property
    def name(self) -> str:
        return "Web Browser Adapter (Chrome/Edge)"

    @property
    def supported_processes(self) -> List[str]:
        return ["chrome.exe", "msedge.exe", "chrome", "edge", "brave.exe", "firefox.exe"]

    async def get_available_actions(self) -> List[str]:
        return [
            "navigate_url",
            "focus_address_bar",
            "find_in_page",
            "new_tab",
            "close_tab",
            "reload_page",
        ]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "focus_address_bar":
            return {"success": True, "hotkey": ["ctrl", "l"], "action": action_name}

        if action_name == "navigate_url":
            url = parameters.get("url", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "l"]},
                    {"type": "type_text", "text": f"{url}\n"},
                ],
            }

        if action_name == "find_in_page":
            query = parameters.get("query", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "f"]},
                    {"type": "type_text", "text": f"{query}\n"},
                ],
            }

        if action_name == "new_tab":
            return {"success": True, "hotkey": ["ctrl", "t"], "action": action_name}

        if action_name == "close_tab":
            return {"success": True, "hotkey": ["ctrl", "w"], "action": action_name}

        if action_name == "reload_page":
            return {"success": True, "hotkey": ["ctrl", "r"], "action": action_name}

        return {"success": False, "error": f"Unknown Browser action '{action_name}'"}
