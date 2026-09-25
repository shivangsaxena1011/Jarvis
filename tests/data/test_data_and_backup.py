"""
Tests for Data Governance & Backup Subsystem (Phase 20)
Verifies backup creation, SHA-256 verification, zip-slip protection,
data export, and privacy-compliant zero-trace data deletion.
"""

import json
from pathlib import Path
import tempfile
import zipfile
import pytest

from core.config.app_dirs import AppDirectories
from core.data.backup_manager import BackupManager
from core.data.data_manager import DataManager


@pytest.fixture
def temp_environment():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        app_dirs = AppDirectories(
            root_dir=base,
            config_dir=base / "config",
            data_dir=base / "data",
            logs_dir=base / "logs",
            memory_dir=base / "memory",
            tasks_dir=base / "tasks",
            cache_dir=base / "cache",
            backups_dir=base / "backups",
            skills_dir=base / "skills",
        )
        app_dirs.ensure_dirs()

        # Seed some dummy user data
        (app_dirs.memory_dir / "user_memory.txt").write_text("User likes dark mode and python.", encoding="utf-8")
        (app_dirs.config_dir / "settings.json").write_text('{"theme": "dark"}', encoding="utf-8")
        (app_dirs.cache_dir / "temp_cache.bin").write_bytes(b"temporary cache binary")

        yield app_dirs


def test_backup_create_and_verify(temp_environment):
    app_dirs = temp_environment
    bm = BackupManager(backups_dir=app_dirs.backups_dir)

    backup_path = bm.create_backup(
        backup_name="test_backup",
        include_logs=True,
        destination_dir=app_dirs.backups_dir,
        source_dirs=[app_dirs.config_dir, app_dirs.memory_dir],
    )

    assert backup_path.exists()
    assert backup_path.name == "test_backup.zip"

    # Verify backup
    res = bm.verify_backup(backup_path)
    assert res["valid"] is True
    assert res["manifest_verified"] is True
    assert res["file_count"] >= 2
    assert res["size_bytes"] > 0
    assert res["checksum"] is not None


def test_backup_restore(temp_environment):
    app_dirs = temp_environment
    bm = BackupManager(backups_dir=app_dirs.backups_dir)

    backup_path = bm.create_backup(
        backup_name="restore_test",
        source_dirs=[app_dirs.memory_dir],
    )

    # Restore to a new location
    restore_target = app_dirs.root_dir / "restored_state"
    success = bm.restore_backup(backup_path, target_dir=restore_target, overwrite=True)
    assert success is True

    # Check restored file exists
    restored_memory = list(restore_target.rglob("user_memory.txt"))
    assert len(restored_memory) == 1
    assert restored_memory[0].read_text(encoding="utf-8") == "User likes dark mode and python."


def test_backup_zip_slip_prevention(temp_environment):
    app_dirs = temp_environment
    bm = BackupManager(backups_dir=app_dirs.backups_dir)

    # Create a malicious zip with traversal path
    malicious_zip = app_dirs.backups_dir / "malicious.zip"
    with zipfile.ZipFile(malicious_zip, "w") as zf:
        zf.writestr("../../outside_evil.txt", "evil payload")

    restore_target = app_dirs.root_dir / "restore_sandbox"
    restore_target.mkdir(parents=True, exist_ok=True)

    with pytest.raises(PermissionError) as exc_info:
        bm.restore_backup(malicious_zip, target_dir=restore_target)
    assert "Zip-slip traversal" in str(exc_info.value)


def test_data_export(temp_environment):
    app_dirs = temp_environment
    dm = DataManager(app_dirs=app_dirs)

    # Export to JSON
    export_json = dm.export_user_data(output_path=app_dirs.data_dir / "export.json", export_format="json")
    assert export_json.exists()
    with open(export_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "metadata" in data
    assert data["metadata"]["version"] == "1.0.0"

    # Export to ZIP
    export_zip = dm.export_user_data(output_path=app_dirs.data_dir / "export.zip", export_format="zip")
    assert export_zip.exists()
    assert zipfile.is_zipfile(export_zip)


def test_delete_user_data_confirmation_and_scopes(temp_environment):
    app_dirs = temp_environment
    dm = DataManager(app_dirs=app_dirs)

    # Without confirmation -> must raise ValueError
    with pytest.raises(ValueError):
        dm.delete_user_data(scope="all", confirm=False)

    # Scope: cache
    res_cache = dm.delete_user_data(scope="cache", confirm=True)
    assert res_cache["status"] == "completed"
    assert not (app_dirs.cache_dir / "temp_cache.bin").exists()
    # Memory should still exist
    assert (app_dirs.memory_dir / "user_memory.txt").exists()

    # Scope: memory
    res_mem = dm.delete_user_data(scope="memory", confirm=True)
    assert res_mem["status"] == "completed"
    assert not (app_dirs.memory_dir / "user_memory.txt").exists()
