"""
SHIVANI Filesystem Tools Foundation
Provides controlled directory listing, searching, metadata inspection, and directory creation.
Enforces strict path traversal and system directory boundaries.
"""

import os
import fnmatch
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from core.errors import PermissionDeniedError


PROTECTED_SYSTEM_DIRS = [
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"c:\system volume information",
    r"c:\$recycle.bin",
    "/bin",
    "/sbin",
    "/etc",
    "/usr",
    "/var",
]


def check_protected_path(target_path: Path) -> None:
    """Raises PermissionDeniedError if target resides in a critical OS system directory."""
    resolved_str = str(target_path.resolve()).lower()
    for sys_dir in PROTECTED_SYSTEM_DIRS:
        if resolved_str == sys_dir or resolved_str.startswith(sys_dir + os.sep):
            raise PermissionDeniedError(
                f"Access to protected operating system directory is denied: {target_path}",
                recovery_suggestion="Target a user workspace folder instead of system directories."
            )


class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Directory path to inspect")


class ListDirectoryTool(BaseTool):
    name = "filesystem.list"
    description = "List files and subdirectories at the given path."
    permission_level = RiskLevel.SAFE
    args_schema = ListDirArgs

    async def run(self, path: str = ".") -> List[Dict[str, Any]]:
        target = Path(path).resolve()
        check_protected_path(target)

        if not target.exists():
            raise FileNotFoundError(f"Directory not found: {path}")
        if not target.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {path}")

        entries = []
        for item in target.iterdir():
            try:
                stat = item.stat()
                entries.append({
                    "name": item.name,
                    "is_dir": item.is_dir(),
                    "size_bytes": stat.st_size if not item.is_dir() else 0,
                    "modified": stat.st_mtime
                })
            except Exception:
                continue

        return entries

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "item_count": len(result_data)}


# Backward compatibility alias
class LegacyListDirTool(ListDirectoryTool):
    name = "filesystem.list_dir"


class SearchFilesArgs(BaseModel):
    pattern: str = Field(default="*", description="Glob pattern to search for (e.g. '*.py', '*test*')")
    path: str = Field(default=".", description="Root directory to start search from")
    max_results: int = Field(default=50, description="Max matching files to return")


class SearchFilesTool(BaseTool):
    name = "filesystem.search"
    description = "Search for files and directories matching a glob pattern."
    permission_level = RiskLevel.SAFE
    args_schema = SearchFilesArgs

    async def run(self, pattern: str = "*", path: str = ".", max_results: int = 50) -> List[Dict[str, Any]]:
        target = Path(path).resolve()
        check_protected_path(target)

        if not target.exists():
            raise FileNotFoundError(f"Search root does not exist: {path}")

        matches = []
        for root, dirs, files in os.walk(target):
            # Check protected path on subtrees
            if any(str(Path(root)).lower().startswith(p) for p in PROTECTED_SYSTEM_DIRS):
                dirs[:] = []
                continue

            for name in files + dirs:
                if fnmatch.fnmatch(name, pattern):
                    full_p = Path(root) / name
                    matches.append({
                        "name": name,
                        "path": str(full_p.resolve()),
                        "is_dir": full_p.is_dir(),
                        "size_bytes": full_p.stat().st_size if full_p.is_file() else 0
                    })
                    if len(matches) >= max_results:
                        return matches

        return matches

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": isinstance(result_data, list), "match_count": len(result_data)}


class ReadMetadataArgs(BaseModel):
    path: str = Field(description="Path of file or directory to inspect")


class ReadMetadataTool(BaseTool):
    name = "filesystem.read_metadata"
    description = "Read file or directory metadata (size, permissions, creation/modification timestamps)."
    permission_level = RiskLevel.SAFE
    args_schema = ReadMetadataArgs

    async def run(self, path: str) -> Dict[str, Any]:
        target = Path(path).resolve()
        check_protected_path(target)

        if not target.exists():
            raise FileNotFoundError(f"Target does not exist: {path}")

        stat = target.stat()
        return {
            "path": str(target),
            "name": target.name,
            "is_dir": target.is_dir(),
            "is_file": target.is_file(),
            "size_bytes": stat.st_size if target.is_file() else 0,
            "created_time": stat.st_ctime,
            "modified_time": stat.st_mtime,
            "permissions": oct(stat.st_mode)[-3:],
            "extension": target.suffix
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": "size_bytes" in result_data and "path" in result_data}


class CreateDirectoryArgs(BaseModel):
    path: str = Field(description="Path of directory to create")


class CreateDirectoryTool(BaseTool):
    name = "filesystem.create_directory"
    description = "Create a new directory safely with parent directories as needed."
    permission_level = RiskLevel.SENSITIVE
    args_schema = CreateDirectoryArgs

    async def run(self, path: str) -> Dict[str, Any]:
        target = Path(path).resolve()
        check_protected_path(target)

        target.mkdir(parents=True, exist_ok=True)
        return {
            "path": str(target),
            "created": True
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        target = Path(result_data.get("path", ""))
        exists = target.exists() and target.is_dir()
        return {
            "verified": exists,
            "is_dir": exists
        }


class ReadFileArgs(BaseModel):
    path: str = Field(description="Path to the file to read")
    max_bytes: int = Field(default=50000, description="Max bytes to read")


class ReadFileTool(BaseTool):
    name = "filesystem.read_file"
    description = "Read text content from a file."
    permission_level = RiskLevel.SAFE
    args_schema = ReadFileArgs

    async def run(self, path: str, max_bytes: int = 50000) -> Dict[str, Any]:
        target = Path(path).resolve()
        check_protected_path(target)

        if not target.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not target.is_file():
            raise ValueError(f"Path is not a file: {path}")

        with open(target, "r", encoding="utf-8", errors="replace") as f:
            content = f.read(max_bytes)

        return {
            "path": str(target),
            "content": content,
            "truncated": len(content) >= max_bytes
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": "content" in result_data}


class WriteFileArgs(BaseModel):
    path: str = Field(description="Destination file path")
    content: str = Field(description="Text content to write")
    append: bool = Field(default=False, description="Whether to append to existing content")


class WriteFileTool(BaseTool):
    name = "filesystem.write_file"
    description = "Write text content to a file."
    permission_level = RiskLevel.SENSITIVE
    args_schema = WriteFileArgs

    async def run(self, path: str, content: str, append: bool = False) -> Dict[str, Any]:
        target = Path(path).resolve()
        check_protected_path(target)

        target.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(target, mode, encoding="utf-8") as f:
            f.write(content)

        return {
            "path": str(target),
            "bytes_written": len(content.encode("utf-8")),
            "mode": mode
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        target = Path(result_data.get("path", ""))
        exists = target.exists()
        return {
            "verified": exists,
            "file_exists": exists,
            "size_bytes": target.stat().st_size if exists else 0
        }
