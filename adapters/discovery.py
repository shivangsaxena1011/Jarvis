"""
SHIVANI Application Discovery
Locates installed desktop applications, Windows Store apps, and PATH executables.
"""

import logging
import os
from pathlib import Path
import shutil
from typing import Dict, List, Optional

from adapters.base import AppInfo

logger = logging.getLogger("shivani.adapters.discovery")


class AppDiscovery:
    """Discovers installed applications on the host system."""

    COMMON_APPS = {
        "vscode": ["code.cmd", "code.exe", "Code.exe"],
        "chrome": ["chrome.exe", "google-chrome"],
        "firefox": ["firefox.exe"],
        "edge": ["msedge.exe"],
        "notepad": ["notepad.exe"],
        "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
        "calculator": ["calc.exe"],
        "explorer": ["explorer.exe"],
        "spotify": ["spotify.exe"],
        "slack": ["slack.exe"],
        "discord": ["discord.exe"],
    }

    def __init__(self):
        self._cache: Dict[str, AppInfo] = {}

    def discover_installed_apps(self, refresh: bool = False) -> List[AppInfo]:
        """Scans PATH and standard application installation directories."""
        if self._cache and not refresh:
            return list(self._cache.values())

        discovered: Dict[str, AppInfo] = {}

        # 1. Search PATH for common application executables
        for app_name, aliases in self.COMMON_APPS.items():
            for alias in aliases:
                path = shutil.which(alias)
                if path:
                    discovered[app_name] = AppInfo(
                        name=app_name,
                        display_name=app_name.capitalize(),
                        executable_path=path,
                        app_type="desktop",
                        supported_actions=["launch", "focus", "close"],
                    )
                    break

        # 2. Check Windows Registry App Paths if on Windows
        if os.name == "nt":
            try:
                import winreg
                reg_paths = [
                    (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
                    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\App Paths"),
                ]
                for hive, subkey in reg_paths:
                    try:
                        with winreg.OpenKey(hive, subkey) as key:
                            num_subkeys = winreg.QueryInfoKey(key)[0]
                            for i in range(min(num_subkeys, 100)):
                                app_exe = winreg.EnumKey(key, i)
                                try:
                                    with winreg.OpenKey(key, app_exe) as app_key:
                                        exe_path, _ = winreg.QueryValueEx(app_key, "")
                                        if exe_path and os.path.exists(exe_path):
                                            name = app_exe.lower().replace(".exe", "")
                                            if name not in discovered:
                                                discovered[name] = AppInfo(
                                                    name=name,
                                                    display_name=name.capitalize(),
                                                    executable_path=exe_path,
                                                    app_type="desktop",
                                                    supported_actions=["launch", "focus", "close"],
                                                )
                                except Exception:
                                    continue
                    except Exception:
                        continue
            except ImportError:
                pass

        self._cache = discovered
        return list(discovered.values())

    def find_app(self, query: str) -> Optional[AppInfo]:
        """Finds application by fuzzy or exact name match."""
        apps = self.discover_installed_apps()
        q = query.lower().strip()
        for app in apps:
            if app.name == q or app.display_name.lower() == q:
                return app
        for app in apps:
            if q in app.name or q in app.display_name.lower():
                return app
        return None
