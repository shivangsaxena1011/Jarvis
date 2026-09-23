"""
SHIVANI File Explorer & Document Finding Tools
Enables opening standard directories (Downloads, Documents, Desktop) in File Explorer
and direct filesystem searching (e.g. for PDFs or recent files) rather than fragile UI clicking.
"""

import os
import glob
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel


class OpenFolderArgs(BaseModel):
    folder_name: str = Field(description="Name or alias of folder to open (e.g. 'downloads', 'documents', 'desktop', or full path)")


class OpenFolderTool(BaseTool):
    name = "computer.open_folder"
    description = "Open a folder in Windows File Explorer (e.g. Downloads, Documents, Desktop)."
    permission_level = RiskLevel.SAFE
    args_schema = OpenFolderArgs
    timeout = 10.0

    def _resolve_standard_path(self, folder_name: str) -> Path:
        clean = folder_name.lower().strip()
        user_home = Path.home()

        folder_aliases = {
            "downloads": user_home / "Downloads",
            "download": user_home / "Downloads",
            "documents": user_home / "Documents",
            "document": user_home / "Documents",
            "desktop": user_home / "Desktop",
            "pictures": user_home / "Pictures",
            "music": user_home / "Music",
            "videos": user_home / "Videos",
        }

        if clean in folder_aliases:
            target = folder_aliases[clean]
            target.mkdir(parents=True, exist_ok=True)
            return target

        # Direct path
        p = Path(folder_name).resolve()
        if p.exists() and p.is_dir():
            return p

        # Fallback to user home
        return user_home

    async def run(self, folder_name: str) -> Dict[str, Any]:
        target_path = self._resolve_standard_path(folder_name)
        
        # Launch Windows File Explorer targeting the folder
        subprocess.Popen(["explorer.exe", str(target_path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        return {
            "folder_requested": folder_name,
            "resolved_path": str(target_path),
            "status": "opened_in_explorer"
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        path = Path(result_data.get("resolved_path", ""))
        exists = path.exists() and path.is_dir()
        return {
            "verified": exists,
            "folder_exists": exists,
            "path": str(path)
        }


class FindFilesArgs(BaseModel):
    pattern: str = Field(default="*.pdf", description="Glob pattern or extension to search (e.g. '*.pdf', '*.docx', '*.txt')")
    folder: Optional[str] = Field(default=None, description="Starting folder alias (e.g. 'downloads', 'documents', or directory path)")
    limit: int = Field(default=10, description="Maximum number of files to return")
    sort_by_recent: bool = Field(default=True, description="Whether to sort files by most recently modified first")


class FindFilesTool(BaseTool):
    name = "computer.find_files"
    description = "Search for files by pattern (e.g. PDF files, documents) across common folders without UI clicking."
    permission_level = RiskLevel.SAFE
    args_schema = FindFilesArgs
    timeout = 15.0

    def _resolve_search_dir(self, folder: Optional[str]) -> Path:
        if not folder:
            return Path.home()
        clean = folder.lower().strip()
        user_home = Path.home()
        folder_aliases = {
            "downloads": user_home / "Downloads",
            "documents": user_home / "Documents",
            "desktop": user_home / "Desktop",
            "pictures": user_home / "Pictures",
        }
        if clean in folder_aliases:
            return folder_aliases[clean]
        p = Path(folder).resolve()
        return p if p.exists() else user_home

    async def run(
        self,
        pattern: str = "*.pdf",
        folder: Optional[str] = None,
        limit: int = 10,
        sort_by_recent: bool = True
    ) -> List[Dict[str, Any]]:
        search_root = self._resolve_search_dir(folder)
        results = []

        # Clean search pattern
        glob_pat = pattern if "*" in pattern else f"*{pattern}"
        if not glob_pat.startswith("*") and not glob_pat.startswith("."):
            glob_pat = f"*{glob_pat}"

        try:
            # Walk directory with depth limit to prevent hanging
            for root, _, files in os.walk(search_root):
                # Don't recurse excessively deep into hidden/system dirs
                rel_depth = len(Path(root).relative_to(search_root).parts)
                if rel_depth > 3:
                    continue
                if any(part.startswith(".") or part in ("node_modules", "AppData", "venv", ".venv") for part in Path(root).parts):
                    continue

                for f in files:
                    import fnmatch
                    if fnmatch.fnmatch(f.lower(), glob_pat.lower()):
                        full_path = Path(root) / f
                        try:
                            st = full_path.stat()
                            results.append({
                                "name": f,
                                "path": str(full_path),
                                "size_bytes": st.st_size,
                                "modified_timestamp": st.st_mtime
                            })
                        except Exception:
                            continue
        except Exception:
            pass

        if sort_by_recent:
            results.sort(key=lambda x: x["modified_timestamp"], reverse=True)

        return results[:limit]

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "matches_found": len(result_data)}
