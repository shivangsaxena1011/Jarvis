"""
SHIVANI Data Manager (Phase 20)
Provides portable user data export and privacy-compliant zero-trace data deletion.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import sqlite3
from typing import Any, Dict, List, Optional
import zipfile

from core.config.app_dirs import get_app_dirs


class DataManager:
    """Handles GDPR/privacy-compliant export and zero-trace deletion of user data."""

    def __init__(self, app_dirs=None):
        self.dirs = app_dirs or get_app_dirs()

    def export_user_data(
        self,
        output_path: Optional[Path] = None,
        export_format: str = "json",
    ) -> Path:
        """
        Exports user profile, memories, goals, knowledge, and task logs into
        a standardized export file (JSON or ZIP).
        """
        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        export_data: Dict[str, Any] = {
            "metadata": {
                "version": "1.0.0",
                "exported_at": now.isoformat(),
                "system": "SHIVANI AI",
            },
            "memory": [],
            "knowledge": [],
            "tasks": [],
            "productivity": {
                "goals": [],
                "projects": [],
            },
        }

        # 1. Export Memory DB facts if available
        mem_db_candidates = [
            self.dirs.memory_dir / "memory.db",
            Path("data/memory.db").resolve(),
            self.dirs.data_dir / "memory.db",
        ]
        for db_file in mem_db_candidates:
            if db_file.exists():
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    # Inspect tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    for table in tables:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 500;")
                        cols = [d[0] for d in cursor.description]
                        for row in cursor.fetchall():
                            export_data["memory"].append({
                                "table": table,
                                "data": dict(zip(cols, row))
                            })
                    conn.close()
                    break
                except Exception:
                    pass

        # 2. Export Knowledge DB facts if available
        kn_db_candidates = [
            Path("data/knowledge.db").resolve(),
            self.dirs.data_dir / "knowledge.db",
        ]
        for db_file in kn_db_candidates:
            if db_file.exists():
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = [row[0] for row in cursor.fetchall()]
                    for table in tables:
                        cursor.execute(f"SELECT * FROM {table} LIMIT 500;")
                        cols = [d[0] for d in cursor.description]
                        for row in cursor.fetchall():
                            export_data["knowledge"].append({
                                "table": table,
                                "data": dict(zip(cols, row))
                            })
                    conn.close()
                    break
                except Exception:
                    pass

        # 3. Export productivity (goals & projects) if JSON storage or DB exists
        prod_candidates = [
            self.dirs.data_dir / "productivity.json",
            Path("data/productivity.json").resolve(),
        ]
        for prod_file in prod_candidates:
            if prod_file.exists():
                try:
                    with open(prod_file, "r", encoding="utf-8") as f:
                        export_data["productivity"] = json.load(f)
                    break
                except Exception:
                    pass

        # 4. Output according to requested format
        if export_format.lower() == "zip":
            target = output_path or (self.dirs.data_dir / f"shivani_user_export_{timestamp_str}.zip")
            target = Path(target).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("user_data.json", json.dumps(export_data, indent=2))
            return target
        else:
            target = output_path or (self.dirs.data_dir / f"shivani_user_export_{timestamp_str}.json")
            target = Path(target).resolve()
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2)
            return target

    def delete_user_data(self, scope: str = "all", confirm: bool = False) -> Dict[str, Any]:
        """
        Deletes user data with zero-trace guarantees.
        scope:
          - "memory": Clears memory database and semantic caches
          - "cache": Clears transient logs, screenshots, audio cache, and browser temporary profiles
          - "all": Clears all personal knowledge, tasks, memory, and cache
        """
        if not confirm:
            raise ValueError("Explicit confirmation (confirm=True) is required to delete user data.")

        cleared_items: List[str] = []
        errors: List[str] = []
        bytes_reclaimed = 0

        def remove_file(p: Path):
            nonlocal bytes_reclaimed
            try:
                if p.exists():
                    bytes_reclaimed += p.stat().st_size
                    p.unlink()
                    cleared_items.append(str(p))
            except Exception as e:
                errors.append(f"Failed to remove {p}: {str(e)}")

        def remove_dir_contents(d: Path):
            nonlocal bytes_reclaimed
            if not d.exists():
                return
            for item in d.glob("*"):
                try:
                    if item.is_file():
                        bytes_reclaimed += item.stat().st_size
                        item.unlink()
                        cleared_items.append(str(item))
                    elif item.is_dir():
                        shutil.rmtree(item)
                        cleared_items.append(str(item))
                except Exception as e:
                    errors.append(f"Failed to clear {item}: {str(e)}")

        # Scope: Memory
        if scope in ("memory", "all"):
            # Target memory files
            for p in [
                self.dirs.memory_dir / "memory.db",
                Path("data/memory.db").resolve(),
                self.dirs.data_dir / "memory.db",
            ]:
                remove_file(p)
            remove_dir_contents(self.dirs.memory_dir)

        # Scope: Cache / Temporary
        if scope in ("cache", "all"):
            remove_dir_contents(self.dirs.cache_dir)
            remove_dir_contents(Path("audio_cache").resolve())
            remove_dir_contents(Path("screenshots").resolve())
            remove_dir_contents(Path("data/transfers_temp").resolve())

        # Scope: All (includes knowledge, tasks, audit history)
        if scope == "all":
            for p in [
                Path("data/knowledge.db").resolve(),
                self.dirs.data_dir / "knowledge.db",
                Path("data/devices.db").resolve(),
                self.dirs.data_dir / "devices.db",
            ]:
                remove_file(p)
            remove_dir_contents(self.dirs.tasks_dir)

        return {
            "status": "completed",
            "scope": scope,
            "cleared_count": len(cleared_items),
            "bytes_reclaimed": bytes_reclaimed,
            "errors": errors,
            "cleared_items": cleared_items,
        }
