"""
SHIVANI Notepad Application Adapter (Phase 17).
Provides text editing, save, and append shortcuts for Windows Notepad.
"""

from __future__ import annotations
from typing import Any, Dict, List
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class NotepadAdapter(ApplicationAdapter):
    """Specialized adapter for Windows Notepad."""

    @property
    def name(self) -> str:
        return "Windows Notepad Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["notepad.exe", "notepad"]

    async def get_available_actions(self) -> List[str]:
        return ["save_file", "select_all", "append_text"]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "save_file":
            return {"success": True, "hotkey": ["ctrl", "s"], "action": action_name}
        if action_name == "select_all":
            return {"success": True, "hotkey": ["ctrl", "a"], "action": action_name}
        if action_name == "append_text":
            text = parameters.get("text", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "end"]},
                    {"type": "type_text", "text": f"\n{text}"},
                ],
            }
        return {"success": False, "error": f"Unknown Notepad action '{action_name}'"}
