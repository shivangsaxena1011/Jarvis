"""
SHIVANI Reversible Operations & Rollback Manager
Creates byte-for-byte pre-action file snapshots to enable 1-click restoration
upon failed edits, incorrect code patches, or execution errors.
"""

from dataclasses import dataclass
import os
from pathlib import Path
import threading
import time
from typing import Dict, List, Optional
import uuid


@dataclass
class FileSnapshot:
    snapshot_id: str
    file_path: str
    original_content: Optional[bytes]
    existed_before: bool
    operation_id: Optional[str]
    timestamp: float


class RollbackManager:
    """Manages pre-execution file snapshots and rollback restoration."""

    def __init__(self, snapshot_dir: Optional[str] = None):
        self.snapshot_dir = Path(snapshot_dir) if snapshot_dir else None
        self._snapshots: Dict[str, FileSnapshot] = {}
        self._op_to_snapshots: Dict[str, List[str]] = {}
        self._lock = threading.Lock()

    def snapshot_file(self, file_path: str, operation_id: Optional[str] = None) -> FileSnapshot:
        """Takes a snapshot of target file before modification."""
        norm_path = os.path.normpath(os.path.abspath(str(file_path)))
        p = Path(norm_path)
        existed = p.exists()
        content = p.read_bytes() if existed else None

        snap = FileSnapshot(

            snapshot_id=str(uuid.uuid4()),
            file_path=norm_path,
            original_content=content,
            existed_before=existed,
            operation_id=operation_id,
            timestamp=time.time(),
        )

        with self._lock:
            self._snapshots[snap.snapshot_id] = snap
            if operation_id:
                if operation_id not in self._op_to_snapshots:
                    self._op_to_snapshots[operation_id] = []
                self._op_to_snapshots[operation_id].append(snap.snapshot_id)

        return snap

    def rollback_snapshot(self, snapshot_id: str) -> bool:
        """Restores a single snapshot to its original byte state."""
        with self._lock:
            snap = self._snapshots.get(snapshot_id)
            if not snap:
                return False

        p = Path(snap.file_path)
        try:
            if snap.existed_before and snap.original_content is not None:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(snap.original_content)
            elif not snap.existed_before and p.exists():
                p.unlink()
            return True
        except Exception:
            return False

    def rollback_operation(self, operation_id: str) -> bool:
        """Restores all snapshots associated with an operation in reverse order."""
        with self._lock:
            snap_ids = list(self._op_to_snapshots.get(operation_id, []))

        success = True
        for sid in reversed(snap_ids):
            if not self.rollback_snapshot(sid):
                success = False

        with self._lock:
            self._op_to_snapshots.pop(operation_id, None)

        return success

    def commit_operation(self, operation_id: str) -> None:
        """Discards snapshots once operation is verified successfully."""
        with self._lock:
            snap_ids = self._op_to_snapshots.pop(operation_id, [])
            for sid in snap_ids:
                self._snapshots.pop(sid, None)

    # Aliases
    create_snapshot = snapshot_file
    rollback = rollback_snapshot

