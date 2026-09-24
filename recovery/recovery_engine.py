"""
SHIVANI Master Recovery Engine
Coordinates task state recovery, rollback management, transactional execution,
and backup creation into a single unified recovery interface.
"""

from typing import Any, Callable, Dict, List, Optional
from recovery.checkpoint_manager import CheckpointManager, TaskCheckpoint
from recovery.rollback_manager import RollbackManager
from recovery.transaction_manager import TransactionManager
from recovery.backup_manager import BackupManager


class RecoveryEngine:
    def __init__(
        self,
        checkpoints_dir: Optional[str] = None,
        backup_dir: Optional[str] = None,
    ):
        self.checkpoints = CheckpointManager(checkpoints_dir=checkpoints_dir)
        self.rollbacks = RollbackManager()
        self.transactions = TransactionManager(rollback_manager=self.rollbacks)
        self.backups = BackupManager(backup_dir=backup_dir)

    def detect_interrupted_tasks(self) -> List[TaskCheckpoint]:
        return self.checkpoints.list_interrupted_tasks()

    def get_task_checkpoint(self, task_id: str) -> Optional[TaskCheckpoint]:
        return self.checkpoints.get_checkpoint(task_id)

    def mark_task_recovering(self, task_id: str) -> Optional[TaskCheckpoint]:
        chk = self.checkpoints.get_checkpoint(task_id)
        if chk:
            chk.status = "RECOVERING"
            chk.retry_count += 1
            return self.checkpoints.save_checkpoint(chk)
        return None

    def mark_task_completed(self, task_id: str) -> None:
        self.checkpoints.clear_checkpoint(task_id)

    def get_status(self) -> Dict[str, Any]:
        interrupted = self.detect_interrupted_tasks()
        backups = self.backups.list_backups()
        return {
            "interrupted_task_count": len(interrupted),
            "interrupted_tasks": [t.task_id for t in interrupted],
            "backup_count": len(backups),
            "status": "operational",
        }
