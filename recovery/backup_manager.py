"""
SHIVANI Backup Manager
Creates timestamped directory archive backups and individual file backups before major operations.
"""

from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional
import zipfile


class BackupManager:
    def __init__(self, backup_dir: Optional[str] = None, backup_root: Optional[str] = None):
        target = backup_root or backup_dir
        if target:
            self.backup_dir = Path(target)
        else:
            base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "Shivani" / "backups"
            self.backup_dir = base
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_file(self, file_path: str) -> Optional[Path]:
        p = Path(file_path)
        if not p.exists():
            return None
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest = self.backup_dir / f"{p.name}.{ts}.bak"
        try:
            shutil.copy2(p, dest)
            return dest
        except Exception:
            return None

    def backup_directory(self, dir_path: str, label: str = "project") -> Optional[Path]:
        p = Path(dir_path)
        if not p.exists() or not p.is_dir():
            return None
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_path = self.backup_dir / f"{label}_{ts}.zip"
        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(p):
                    for file in files:
                        full_p = Path(root) / file
                        arcname = full_p.relative_to(p)
                        zf.write(full_p, arcname=arcname)
            return zip_path
        except Exception:
            return None

    # Alias
    create_directory_backup = backup_directory

    def list_backups(self) -> List[Dict[str, Any]]:
        backups = []
        for f in sorted(self.backup_dir.iterdir(), key=os.path.getmtime, reverse=True):
            backups.append({
                "name": f.name,
                "path": str(f),
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
        return backups
