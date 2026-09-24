"""
Phase 9 Recovery & Idempotency Test Suite
Verifies byte-for-byte rollback, multi-file atomic transactions,
task crash checkpoints, and idempotency deduplication.
"""

import os
import tempfile
from pathlib import Path
import pytest

from recovery.rollback_manager import RollbackManager
from recovery.transaction_manager import TransactionManager
from recovery.checkpoint_manager import CheckpointManager
from recovery.backup_manager import BackupManager
from core.idempotency import IdempotencyManager, ExecutionState


def test_file_snapshot_and_rollback():
    with tempfile.TemporaryDirectory() as tmpdir:
        rb = RollbackManager(snapshot_dir=tmpdir)
        test_file = Path(tmpdir) / "document.txt"
        original_content = "This is original critical content.\nLine 2.\n"
        test_file.write_text(original_content, encoding="utf-8")

        # Snapshot before action
        snap = rb.create_snapshot(test_file)
        assert snap is not None

        # Corrupt / modify the file
        test_file.write_text("CORRUPTED BY FAILED OPERATION", encoding="utf-8")
        assert test_file.read_text(encoding="utf-8") != original_content

        # Rollback
        restored = rb.rollback(snap.snapshot_id)
        assert restored is True
        assert test_file.read_text(encoding="utf-8") == original_content


def test_atomic_transaction_rollback_on_failure():
    with tempfile.TemporaryDirectory() as tmpdir:
        f1 = Path(tmpdir) / "file1.txt"
        f2 = Path(tmpdir) / "file2.txt"
        f1.write_text("orig1", encoding="utf-8")
        f2.write_text("orig2", encoding="utf-8")

        # Run transaction that fails midway
        try:
            with TransactionManager(snapshot_dir=tmpdir) as tx:
                tx.stage_file(f1)
                tx.stage_file(f2)

                f1.write_text("mutated1", encoding="utf-8")
                f2.write_text("mutated2", encoding="utf-8")

                raise RuntimeError("Simulated mid-operation failure!")
        except RuntimeError:
            pass

        # Files must be rolled back to original states
        assert f1.read_text(encoding="utf-8") == "orig1"
        assert f2.read_text(encoding="utf-8") == "orig2"


def test_task_checkpoint_and_interrupted_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        cm = CheckpointManager(checkpoint_dir=tmpdir)

        task_id = "task-alpha-123"
        cm.save_checkpoint(
            task_id=task_id,
            stage="EXECUTING_STEP",
            step_index=2,
            total_steps=5,
            state={"query": "Automate report generation", "completed_steps": ["step1", "step2"]},
        )

        # Detect interrupted tasks
        interrupted = cm.list_interrupted_tasks()
        assert len(interrupted) == 1
        assert interrupted[0]["task_id"] == task_id
        assert interrupted[0]["step_index"] == 2

        # Mark completed and verify cleared
        cm.clear_checkpoint(task_id)
        assert len(cm.list_interrupted_tasks()) == 0


def test_idempotency_manager_duplicate_deduplication():
    im = IdempotencyManager()

    tool_name = "gmail_send_email"
    args = {"to": "boss@example.com", "subject": "Quarterly Report", "body": "Attached"}

    # Register initial execution
    is_dupe, rec = im.check_or_register(tool_name, args)
    assert is_dupe is False
    assert rec.state == ExecutionState.PENDING

    # Transition to COMPLETED
    im.record_result(rec.operation_id, result={"status": "sent", "message_id": "msg_999"}, state=ExecutionState.COMPLETED)

    # Attempt duplicate execution
    is_dupe_2, rec_2 = im.check_or_register(tool_name, args)
    assert is_dupe_2 is True
    assert rec_2.result == {"status": "sent", "message_id": "msg_999"}
    assert rec_2.state == ExecutionState.COMPLETED


def test_backup_manager_directory_archive():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "source"
        src.mkdir()
        (src / "data.csv").write_text("1,2,3", encoding="utf-8")

        backup_dir = Path(tmpdir) / "backups"
        bm = BackupManager(backup_root=backup_dir)

        archive = bm.create_directory_backup(src, label="test_backup")
        assert archive.exists()
        assert archive.stat().st_size > 0
