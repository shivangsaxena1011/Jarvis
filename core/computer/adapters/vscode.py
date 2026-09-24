"""
SHIVANI Visual Studio Code Application Adapter (Phase 17).
Provides specialized semantic actions for VS Code: workspace navigation,
quick open, command palette, terminal toggle, and test execution.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class VSCodeAdapter(ApplicationAdapter):
    """Specialized adapter for Visual Studio Code."""

    @property
    def name(self) -> str:
        return "Visual Studio Code Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["code.exe", "code", "visual studio code"]

    async def get_available_actions(self) -> List[str]:
        return [
            "open_file",
            "open_command_palette",
            "toggle_terminal",
            "run_tests",
            "search_symbol",
            "save_all",
        ]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "open_command_palette":
            # Ctrl+Shift+P
            return {"success": True, "hotkey": ["ctrl", "shift", "p"], "action": action_name}

        if action_name == "open_file":
            filename = parameters.get("filename", "")
            # Ctrl+P, then type filename, then Enter
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "p"]},
                    {"type": "type_text", "text": filename},
                    {"type": "key_press", "key": "enter"},
                ],
            }

        if action_name == "toggle_terminal":
            # Ctrl+`
            return {"success": True, "hotkey": ["ctrl", "`"], "action": action_name}

        if action_name == "run_tests":
            test_target = parameters.get("test_target", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "`"]},
                    {"type": "type_text", "text": f"pytest {test_target}\n"},
                ],
            }

        if action_name == "save_all":
            # Ctrl+K, S
            return {"success": True, "hotkey": ["ctrl", "k", "s"], "action": action_name}

        return {"success": False, "error": f"Unknown VSCode action '{action_name}'"}
