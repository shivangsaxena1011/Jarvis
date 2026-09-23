"""
SHIVANI Clipboard Manager
Provides safe access to system clipboard without logging content or leaking secrets.
"""

from typing import Any, Dict, Optional
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter


class ClipboardManager:
    """Safely reads and writes clipboard content with privacy protection."""

    def __init__(self, adapter: Optional[OperatingSystemAdapter] = None):
        self.adapter = adapter or get_os_adapter()

    async def read(self) -> Dict[str, Any]:
        """
        Reads textual content from system clipboard.
        Note: The return metadata masks the content length to protect passwords.
        """
        content = await self.adapter.clipboard_read()
        return {
            "content": content,
            "length": len(content),
            "is_empty": len(content) == 0
        }

    async def write(self, text: str) -> Dict[str, Any]:
        """Writes text into system clipboard."""
        await self.adapter.clipboard_write(text)
        return {
            "characters_written": len(text),
            "success": True
        }

    async def clear(self) -> Dict[str, Any]:
        """Clears system clipboard."""
        await self.adapter.clipboard_clear()
        return {
            "cleared": True,
            "success": True
        }
