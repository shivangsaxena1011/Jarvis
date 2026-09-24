"""
SHIVANI Terminal & Shell Application Adapter (Phase 17).
Provides specialized keyboard navigation, clear, interrupt,
and shell shortcuts for Windows Terminal / PowerShell / Command Prompt.
"""

from __future__ import annotations
from typing import Any, Dict, List
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class TerminalAdapter(ApplicationAdapter):
    """Specialized adapter for Windows Terminal, PowerShell, and CMD."""

    @property
    def name(self) -> str:
        return "Windows Terminal Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return [
            "windowsterminal.exe",
            "wt.exe",
            "powershell.exe",
            "pwsh.exe",
            "cmd.exe",
            "terminal",
        ]

    async def get_available_actions(self) -> List[str]:
        return [
            "interrupt_command",
            "clear_screen",
            "split_pane",
            "new_tab",
            "paste_command",
        ]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "interrupt_command":
            # Ctrl+C
            return {"success": True, "hotkey": ["ctrl", "c"], "action": action_name}

        if action_name == "clear_screen":
            # Ctrl+L or cls
            return {"success": True, "hotkey": ["ctrl", "l"], "action": action_name}

        if action_name == "split_pane":
            # Alt+Shift+Plus / D
            return {"success": True, "hotkey": ["alt", "shift", "+"], "action": action_name}

        if action_name == "new_tab":
            # Ctrl+Shift+T
            return {"success": True, "hotkey": ["ctrl", "shift", "t"], "action": action_name}

        if action_name == "paste_command":
            cmd = parameters.get("command", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [{"type": "type_text", "text": f"{cmd}\n"}],
            }

        return {"success": False, "error": f"Unknown Terminal action '{action_name}'"}
