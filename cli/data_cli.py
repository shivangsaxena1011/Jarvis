"""
SHIVANI Data & Backup CLI Subsystem (Phase 20)
Provides CLI handlers for `shivani data export`, `delete`, `backup`, `restore`, and `list`.
"""

from pathlib import Path
import sys
from typing import Any

from core.data.backup_manager import BackupManager
from core.data.data_manager import DataManager


def handle_data_cli(args: Any) -> int:
    """Dispatches `shivani data ...` subcommands."""
    action = getattr(args, "data_action", None)
    if not action:
        print("Usage: shivani data [export|delete|backup|verify|restore|list] ...")
        return 0

    if action == "export":
        fmt = getattr(args, "format", "json") or "json"
        out = getattr(args, "output", None)
        out_path = Path(out).resolve() if out else None

        dm = DataManager()
        result_path = dm.export_user_data(output_path=out_path, export_format=fmt)
        print(f"Data export completed successfully.")
        print(f"Export file : {result_path}")
        print(f"File size   : {result_path.stat().st_size} bytes")
        return 0

    elif action == "delete":
        scope = getattr(args, "scope", "all") or "all"
        confirmed = getattr(args, "yes", False)

        if not confirmed:
            print(f"WARNING: You are about to permanently delete user data (scope='{scope}').")
            resp = input("Type 'CONFIRM' to proceed: ").strip()
            if resp != "CONFIRM":
                print("Data deletion cancelled by user.")
                return 1
            confirmed = True

        dm = DataManager()
        result = dm.delete_user_data(scope=scope, confirm=confirmed)
        print(f"Zero-trace data deletion completed (scope: {scope}).")
        print(f"Items cleared   : {result['cleared_count']}")
        print(f"Bytes reclaimed : {result['bytes_reclaimed']} bytes")
        if result["errors"]:
            print(f"Encountered {len(result['errors'])} warnings/errors during wipe.")
        return 0

    elif action == "backup":
        name = getattr(args, "name", None)
        include_logs = getattr(args, "logs", False)

        bm = BackupManager()
        archive_path = bm.create_backup(backup_name=name, include_logs=include_logs)
        verification = bm.verify_backup(archive_path)

        print("=== SHIVANI SYSTEM BACKUP CREATED ===")
        print(f"Archive file: {archive_path}")
        print(f"Size        : {archive_path.stat().st_size} bytes")
        print(f"SHA-256     : {verification.get('checksum')}")
        print(f"Integrity   : {'VERIFIED' if verification.get('valid') else 'FAILED'}")
        return 0

    elif action == "verify":
        path_str = getattr(args, "path", None)
        if not path_str:
            print("Error: --path argument is required for backup verification.")
            return 1

        bm = BackupManager()
        res = bm.verify_backup(Path(path_str))
        if res["valid"]:
            print(f"Backup integrity verified: {path_str}")
            print(f"Files in archive : {res.get('file_count')}")
            print(f"Archive size     : {res.get('size_bytes')} bytes")
            print(f"SHA-256 Checksum : {res.get('checksum')}")
            print(f"Manifest Match   : {res.get('manifest_verified')}")
            return 0
        else:
            print(f"Backup verification failed: {res.get('error')}")
            return 1

    elif action == "restore":
        path_str = getattr(args, "path", None)
        overwrite = getattr(args, "overwrite", False)
        target = getattr(args, "target", None)
        if not path_str:
            print("Error: --path argument is required for backup restoration.")
            return 1

        bm = BackupManager()
        try:
            target_path = Path(target).resolve() if target else None
            bm.restore_backup(Path(path_str), target_dir=target_path, overwrite=overwrite)
            print(f"Backup restored successfully from: {path_str}")
            return 0
        except Exception as e:
            print(f"Restoration failed: {str(e)}")
            return 1

    elif action == "list":
        bm = BackupManager()
        backups = bm.list_backups()
        print(f"=== SHIVANI BACKUP INVENTORY ({len(backups)} found) ===")
        if not backups:
            print("No backups found.")
            return 0

        for b in backups:
            print(f"- {b['name']:<35} | {b['size_bytes']:>10} bytes | {b['created_at']}")
            if b.get("sha256"):
                print(f"  SHA-256: {b['sha256']}")
        return 0

    else:
        print(f"Unknown data action: {action}")
        return 1
