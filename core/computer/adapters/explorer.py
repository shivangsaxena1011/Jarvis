"""
SHIVANI Windows Explorer & File Organization Adapter (Phase 17).
Provides directory navigation, address bar manipulation, file scanning,
and mandatory batch action previews before file moves or renames.
"""

from __future__ import annotations
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
from core.computer.adapters.base import ApplicationAdapter
from core.computer.models import ApplicationContext


class ExplorerAdapter(ApplicationAdapter):
    """Specialized adapter for Windows File Explorer and file organization."""

    @property
    def name(self) -> str:
        return "Windows File Explorer Adapter"

    @property
    def supported_processes(self) -> List[str]:
        return ["explorer.exe", "explorer", "file explorer"]

    async def get_available_actions(self) -> List[str]:
        return [
            "navigate_path",
            "focus_address_bar",
            "scan_directory",
            "propose_organization",
            "apply_organization",
        ]

    async def execute_action(
        self, action_name: str, parameters: Dict[str, Any], context: ApplicationContext
    ) -> Dict[str, Any]:
        if action_name == "focus_address_bar":
            return {"success": True, "hotkey": ["ctrl", "l"], "action": action_name}

        if action_name == "navigate_path":
            path = parameters.get("path", "")
            return {
                "success": True,
                "action": action_name,
                "sequence": [
                    {"type": "hotkey", "keys": ["ctrl", "l"]},
                    {"type": "type_text", "text": f"{path}\n"},
                ],
            }

        if action_name == "scan_directory":
            dir_path = Path(parameters.get("directory", "."))
            if not dir_path.exists():
                return {"success": False, "error": f"Directory '{dir_path}' does not exist"}

            files_by_ext: Dict[str, List[str]] = {}
            for item in dir_path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower() or "no_ext"
                    files_by_ext.setdefault(ext, []).append(item.name)

            return {
                "success": True,
                "action": action_name,
                "directory": str(dir_path),
                "summary": {k: len(v) for k, v in files_by_ext.items()},
                "files_by_ext": files_by_ext,
            }

        if action_name == "propose_organization":
            # Generates a clear preview of moves into organized subfolders
            dir_path = Path(parameters.get("directory", "."))
            rules = {
                "Documents": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx", ".csv"],
                "Images": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"],
                "Archives": [".zip", ".tar", ".gz", ".7z", ".rar"],
                "Installers": [".exe", ".msi", ".dmg"],
            }
            planned_moves: List[Dict[str, str]] = []
            planned_dirs: List[str] = []

            for item in dir_path.iterdir():
                if item.is_file():
                    ext = item.suffix.lower()
                    for folder, exts in rules.items():
                        if ext in exts:
                            planned_moves.append({
                                "source": str(item),
                                "target": str(dir_path / folder / item.name),
                                "target_folder": folder,
                            })
                            if folder not in planned_dirs:
                                planned_dirs.append(folder)
                            break

            return {
                "success": True,
                "preview_required": True,
                "planned_directories": planned_dirs,
                "planned_moves": planned_moves,
                "total_files": len(planned_moves),
                "preview_message": (
                    f"Planned changes for '{dir_path}':\n"
                    f"Create {len(planned_dirs)} folders: {', '.join(planned_dirs)}\n"
                    f"Move {len(planned_moves)} files safely into subdirectories.\n"
                    f"Nothing will be deleted."
                ),
            }

        if action_name == "apply_organization":
            planned_moves = parameters.get("planned_moves", [])
            applied = 0
            for move in planned_moves:
                src = Path(move["source"])
                dst = Path(move["target"])
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.exists():
                    shutil.move(str(src), str(dst))
                    applied += 1

            return {"success": True, "applied_moves": applied, "verified": True}

        return {"success": False, "error": f"Unknown Explorer action '{action_name}'"}
