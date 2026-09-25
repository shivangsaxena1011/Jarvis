"""
SHIVANI Backup Manager (Phase 20)
Provides automated, verified, and portable backups of user data, memory,
knowledge graphs, and configurations with cryptographic checksums.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Dict, List, Optional
import zipfile

from core.config.app_dirs import get_app_dirs


class BackupManager:
    """Manages the creation, verification, listing, restoration, and deletion of backups."""

    def __init__(self, backups_dir: Optional[Path] = None):
        if backups_dir:
            self.backups_dir = Path(backups_dir)
        else:
            self.backups_dir = get_app_dirs().backups_dir
        self.backups_dir.mkdir(parents=True, exist_ok=True)

    def _compute_sha256(self, file_path: Path) -> str:
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def create_backup(
        self,
        backup_name: Optional[str] = None,
        include_logs: bool = False,
        destination_dir: Optional[Path] = None,
        source_dirs: Optional[List[Path]] = None,
    ) -> Path:
        """
        Creates a timestamped compressed backup archive of user data and state.
        Returns the absolute path to the generated backup archive.
        """
        target_dir = Path(destination_dir) if destination_dir else self.backups_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        now = datetime.now(timezone.utc)
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        name = backup_name or f"shivani_backup_{timestamp_str}"
        if not name.endswith(".zip"):
            archive_filename = f"{name}.zip"
        else:
            archive_filename = name

        archive_path = target_dir / archive_filename
        dirs = get_app_dirs()

        if source_dirs is None:
            # Default directories to back up
            source_dirs = [
                dirs.data_dir,
                dirs.memory_dir,
                dirs.config_dir,
                dirs.tasks_dir,
            ]
            if include_logs:
                source_dirs.append(dirs.logs_dir)

            # Also check local project directory data/ if app_dirs are empty or running locally
            local_data = Path("data").resolve()
            if local_data.exists() and local_data not in source_dirs:
                source_dirs.append(local_data)

        files_archived = []
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for s_dir in source_dirs:
                s_dir = Path(s_dir).resolve()
                if not s_dir.exists():
                    continue

                if s_dir.is_file():
                    zf.write(s_dir, arcname=s_dir.name)
                    files_archived.append(s_dir.name)
                    continue

                for root, _, files in os.walk(s_dir):
                    for file in files:
                        full_path = Path(root) / file
                        # Don't archive open lock files or temporary sockets
                        if file.endswith((".lock", ".tmp", ".sock")):
                            continue
                        rel_path = full_path.relative_to(s_dir.parent)
                        zf.write(full_path, arcname=str(rel_path))
                        files_archived.append(str(rel_path))

        # Generate cryptographic checksum & metadata manifest
        checksum = self._compute_sha256(archive_path)
        manifest_data = {
            "backup_name": archive_filename,
            "created_at": now.isoformat(),
            "sha256": checksum,
            "file_count": len(files_archived),
            "size_bytes": archive_path.stat().st_size,
            "included_logs": include_logs,
            "version": "1.0.0",
        }

        manifest_path = target_dir / f"{archive_filename}.manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)

        return archive_path

    def verify_backup(self, backup_path: Path) -> Dict[str, object]:
        """
        Verifies backup integrity: checks zip structure and compares SHA-256 against manifest.
        """
        backup_path = Path(backup_path).resolve()
        if not backup_path.exists():
            return {
                "valid": False,
                "error": f"Backup file not found: {backup_path}",
                "size_bytes": 0,
                "file_count": 0,
            }

        # 1. Verify zip structure
        try:
            with zipfile.ZipFile(backup_path, "r") as zf:
                bad_file = zf.testzip()
                if bad_file:
                    return {
                        "valid": False,
                        "error": f"Corrupted file in archive: {bad_file}",
                        "size_bytes": backup_path.stat().st_size,
                    }
                file_count = len(zf.namelist())
        except Exception as e:
            return {
                "valid": False,
                "error": f"Invalid zip archive: {str(e)}",
                "size_bytes": backup_path.stat().st_size,
            }

        # 2. Verify SHA-256 Checksum against manifest if present
        current_checksum = self._compute_sha256(backup_path)
        manifest_path = backup_path.parent / f"{backup_path.name}.manifest.json"

        manifest_verified = None
        if manifest_path.exists():
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)
                expected_sha = manifest.get("sha256")
                manifest_verified = (current_checksum == expected_sha)
                if not manifest_verified:
                    return {
                        "valid": False,
                        "error": f"Checksum mismatch: expected {expected_sha}, computed {current_checksum}",
                        "checksum": current_checksum,
                        "manifest_verified": False,
                        "file_count": file_count,
                        "size_bytes": backup_path.stat().st_size,
                    }
            except Exception as e:
                manifest_verified = False

        return {
            "valid": True,
            "error": None,
            "checksum": current_checksum,
            "manifest_verified": manifest_verified,
            "file_count": file_count,
            "size_bytes": backup_path.stat().st_size,
        }

    def list_backups(self, backups_dir: Optional[Path] = None) -> List[Dict[str, object]]:
        """Lists all existing backups with metadata and verification status."""
        target_dir = Path(backups_dir) if backups_dir else self.backups_dir
        if not target_dir.exists():
            return []

        results = []
        for file in target_dir.glob("*.zip"):
            stat = file.stat()
            manifest_file = target_dir / f"{file.name}.manifest.json"
            meta = {}
            if manifest_file.exists():
                try:
                    with open(manifest_file, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            results.append({
                "name": file.name,
                "path": str(file.resolve()),
                "size_bytes": stat.st_size,
                "created_at": meta.get("created_at") or datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "sha256": meta.get("sha256"),
                "file_count": meta.get("file_count"),
                "has_manifest": manifest_file.exists(),
            })

        results.sort(key=lambda x: str(x["created_at"]), reverse=True)
        return results

    def restore_backup(
        self,
        backup_path: Path,
        target_dir: Optional[Path] = None,
        overwrite: bool = False,
    ) -> bool:
        """
        Safely unpacks the backup archive into target_dir (preventing zip-slip traversal).
        """
        backup_path = Path(backup_path).resolve()
        dest = Path(target_dir).resolve() if target_dir else get_app_dirs().root_dir
        dest.mkdir(parents=True, exist_ok=True)

        verification = self.verify_backup(backup_path)
        if not verification["valid"]:
            raise ValueError(f"Cannot restore invalid backup: {verification.get('error')}")

        with zipfile.ZipFile(backup_path, "r") as zf:
            for member in zf.infolist():
                # Guard against zip-slip traversal attacks
                member_path = Path(dest / member.filename).resolve()
                if not str(member_path).startswith(str(dest)):
                    raise PermissionError(f"Zip-slip traversal attempt detected in: {member.filename}")

                if member.is_dir():
                    member_path.mkdir(parents=True, exist_ok=True)
                    continue

                if member_path.exists() and not overwrite:
                    continue

                member_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(member_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        return True

    def delete_backup(self, backup_name_or_path: str, backups_dir: Optional[Path] = None) -> bool:
        """Deletes a backup archive and its accompanying manifest."""
        target_dir = Path(backups_dir) if backups_dir else self.backups_dir
        p = Path(backup_name_or_path)
        if not p.is_absolute():
            p = target_dir / backup_name_or_path

        p = p.resolve()
        if not p.exists():
            return False

        p.unlink()
        manifest_p = p.parent / f"{p.name}.manifest.json"
        if manifest_p.exists():
            manifest_p.unlink()

        return True
