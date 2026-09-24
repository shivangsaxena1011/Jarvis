"""
SHIVANI Transaction Manager
Wraps reversible multi-file operations in atomic transactions with automatic rollback on exception.
Supports both synchronous context manager and async transaction contexts.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator, List, Optional
import uuid
from recovery.rollback_manager import RollbackManager


class TransactionContext:
    def __init__(self, tx_id: str, rollback_manager: RollbackManager):
        self.tx_id = tx_id
        self.rollback_manager = rollback_manager
        self.tracked_files: List[str] = []

    def track_file(self, file_path: str) -> None:
        self.rollback_manager.snapshot_file(file_path=str(file_path), operation_id=self.tx_id)
        self.tracked_files.append(str(file_path))

    # Alias
    stage_file = track_file


class TransactionManager:
    def __init__(self, rollback_manager: Optional[RollbackManager] = None, snapshot_dir: Optional[str] = None):
        self.rollback_manager = rollback_manager or RollbackManager(snapshot_dir=snapshot_dir)
        self._active_ctx: Optional[TransactionContext] = None

    def __enter__(self) -> TransactionContext:
        tx_id = f"tx_{uuid.uuid4().hex[:8]}"
        self._active_ctx = TransactionContext(tx_id=tx_id, rollback_manager=self.rollback_manager)
        return self._active_ctx

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._active_ctx:
            if exc_type is not None:
                self.rollback_manager.rollback_operation(self._active_ctx.tx_id)
            else:
                self.rollback_manager.commit_operation(self._active_ctx.tx_id)
        return False

    @asynccontextmanager
    async def transaction(self, name: str = "tx") -> AsyncIterator[TransactionContext]:
        tx_id = f"{name}_{uuid.uuid4().hex[:8]}"
        ctx = TransactionContext(tx_id=tx_id, rollback_manager=self.rollback_manager)
        try:
            yield ctx
            # Success -> commit snapshots
            self.rollback_manager.commit_operation(tx_id)
        except Exception:
            # Exception -> rollback snapshots
            self.rollback_manager.rollback_operation(tx_id)
            raise
