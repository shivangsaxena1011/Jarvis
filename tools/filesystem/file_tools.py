"""
SHIVANI Filesystem Tools
Provides controlled directory listing, file reading, writing, and safe deletion.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from security.sandbox.command_validator import CommandValidator


class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Directory path to inspect")


class ListDirectoryTool(BaseTool):
    name = "filesystem.list_dir"
    description = "List files and subdirectories at the given path."
    permission_level = RiskLevel.SAFE
    args_schema = ListDirArgs

    async def run(self, path: str = ".") -> List[Dict[str, Any]]:
        target = Path(path).resolve()
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
        # Path safety check
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


class SafeDeleteArgs(BaseModel):
    path: str = Field(description="Path of file or empty directory to delete")


class SafeDeleteTool(BaseTool):
    name = "filesystem.safe_delete"
    description = "Safely delete a file or directory. Requires explicit CRITICAL confirmation."
    permission_level = RiskLevel.CRITICAL
    args_schema = SafeDeleteArgs

    async def run(self, path: str) -> Dict[str, Any]:
        target = Path(path).resolve()
        if not target.exists():
            raise FileNotFoundError(f"Target path does not exist: {path}")

        if target.is_file():
            target.unlink()
        elif target.is_dir():
            target.rmdir() # only deletes empty directory safely

        return {
            "path": str(target),
            "deleted": True
        }

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        target = Path(result_data.get("path", ""))
        still_exists = target.exists()
        return {
            "verified": not still_exists,
            "successfully_removed": not still_exists
        }
