"""
SHIVANI Standard Application Directories Layout
Resolves %APPDATA%\\Shivani (or ~/.shivani) for isolated, production-grade
configuration, credentials, logs, memory, tasks, cache, and backups.
"""

import os
from pathlib import Path
from dataclasses import dataclass


@dataclass
class AppDirectories:
    root_dir: Path
    config_dir: Path
    data_dir: Path
    logs_dir: Path
    memory_dir: Path
    tasks_dir: Path
    cache_dir: Path
    backups_dir: Path
    skills_dir: Path

    def ensure_dirs(self) -> None:
        """Creates all application directories if they do not exist."""
        for path in [
            self.root_dir,
            self.config_dir,
            self.data_dir,
            self.logs_dir,
            self.memory_dir,
            self.tasks_dir,
            self.cache_dir,
            self.backups_dir,
            self.skills_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def get_skill_dir(self, skill_name: str) -> Path:
        """Returns isolated directory for a specific skill: %APPDATA%/Shivani/skills/<skill_name>."""
        p = self.skills_dir / skill_name
        p.mkdir(parents=True, exist_ok=True)
        for sub in ["config", "cache", "logs", "data"]:
            (p / sub).mkdir(parents=True, exist_ok=True)
        return p


def get_app_dirs() -> AppDirectories:
    """
    Computes standard directory layout:
    1. SHIVANI_HOME env var if set
    2. %APPDATA%\\Shivani on Windows
    3. ~/.shivani on Linux/macOS
    """
    override = os.getenv("SHIVANI_HOME")
    if override:
        root = Path(override).resolve()
    elif os.name == "nt":
        appdata = os.getenv("APPDATA")
        if appdata:
            root = Path(appdata) / "Shivani"
        else:
            root = Path.home() / "AppData" / "Roaming" / "Shivani"
    else:
        root = Path.home() / ".shivani"

    return AppDirectories(
        root_dir=root,
        config_dir=root / "config",
        data_dir=root / "data",
        logs_dir=root / "logs",
        memory_dir=root / "memory",
        tasks_dir=root / "tasks",
        cache_dir=root / "cache",
        backups_dir=root / "backups",
        skills_dir=root / "skills",
    )

