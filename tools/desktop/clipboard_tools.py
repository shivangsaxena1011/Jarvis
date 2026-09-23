"""
SHIVANI Clipboard Tools
Provides registered tools for reading, writing, and clearing the system clipboard.
Clipboard content is protected to prevent sensitive data leakage.
"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from tools.base import BaseTool
from security.permissions.engine import RiskLevel
from tools.desktop.clipboard import ClipboardManager


class ClipboardWriteArgs(BaseModel):
    text: str = Field(description="Text to copy into clipboard")


class ClipboardReadTool(BaseTool):
    name = "clipboard.read"
    description = "Read current textual contents from the system clipboard."
    permission_level = RiskLevel.SAFE
    timeout = 3.0

    def __init__(self, clipboard_manager: Optional[ClipboardManager] = None):
        super().__init__()
        self.clipboard_manager = clipboard_manager or ClipboardManager()

    async def run(self) -> Dict[str, Any]:
        return await self.clipboard_manager.read()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": "content" in result_data}


class ClipboardWriteTool(BaseTool):
    name = "clipboard.write"
    description = "Write textual string to the system clipboard."
    permission_level = RiskLevel.SAFE
    args_schema = ClipboardWriteArgs
    timeout = 3.0

    def __init__(self, clipboard_manager: Optional[ClipboardManager] = None):
        super().__init__()
        self.clipboard_manager = clipboard_manager or ClipboardManager()

    async def run(self, text: str) -> Dict[str, Any]:
        return await self.clipboard_manager.write(text)

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}


class ClipboardClearTool(BaseTool):
    name = "clipboard.clear"
    description = "Erase and clear all content from the system clipboard."
    permission_level = RiskLevel.SAFE
    timeout = 3.0

    def __init__(self, clipboard_manager: Optional[ClipboardManager] = None):
        super().__init__()
        self.clipboard_manager = clipboard_manager or ClipboardManager()

    async def run(self) -> Dict[str, Any]:
        return await self.clipboard_manager.clear()

    async def verify(self, result_data: Any, **kwargs: Any) -> Dict[str, Any]:
        return {"verified": result_data.get("success", False)}
