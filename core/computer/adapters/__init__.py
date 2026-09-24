"""
SHIVANI Application Adapters Package (Phase 17).
Exports adapter registry pre-populated with default specialized adapters.
"""

from core.computer.adapters.base import (
    ApplicationAdapter,
    GenericApplicationFallback,
    AdapterRegistry,
)
from core.computer.adapters.vscode import VSCodeAdapter
from core.computer.adapters.explorer import ExplorerAdapter
from core.computer.adapters.terminal import TerminalAdapter
from core.computer.adapters.browser import BrowserAdapter
from core.computer.adapters.office import ExcelAdapter, PowerPointAdapter, WordAdapter
from core.computer.adapters.notepad import NotepadAdapter


def create_default_adapter_registry() -> AdapterRegistry:
    reg = AdapterRegistry()
    reg.register(VSCodeAdapter())
    reg.register(ExplorerAdapter())
    reg.register(TerminalAdapter())
    reg.register(BrowserAdapter())
    reg.register(ExcelAdapter())
    reg.register(PowerPointAdapter())
    reg.register(WordAdapter())
    reg.register(NotepadAdapter())
    return reg


__all__ = [
    "ApplicationAdapter",
    "GenericApplicationFallback",
    "AdapterRegistry",
    "VSCodeAdapter",
    "ExplorerAdapter",
    "TerminalAdapter",
    "BrowserAdapter",
    "ExcelAdapter",
    "PowerPointAdapter",
    "WordAdapter",
    "NotepadAdapter",
    "create_default_adapter_registry",
]
