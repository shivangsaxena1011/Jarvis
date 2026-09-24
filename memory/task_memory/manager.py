"""
SHIVANI Task Memory Manager
Maintains in-flight task states, step checkpoints, and intermediate execution artifacts
to enable recovery, pause, and resumption across complex multi-step workflows.
"""

from typing import Any, Dict, List, Optional
from memory.models import MemoryCategory, MemoryItem, MemoryScope, MemorySource
from memory.storage.sqlite_store import SQLiteMemoryStore


class TaskMemory:
    def __init__(self, store: SQLiteMemoryStore):
        self.store = store

    def save_checkpoint(
        self,
        task_id: str,
        stage: str,
        step_index: int,
        state: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> MemoryItem:
        """Saves a checkpoint for an active or suspended task."""
        payload = {
            "task_id": task_id,
            "stage": stage,
            "step_index": step_index,
            "state": state,
        }
        item = MemoryItem(
            category=MemoryCategory.TASK,
            scope=MemoryScope.TASK,
            scope_id=task_id,
            key=f"checkpoint_{task_id}",
            value=payload,
            confidence=1.0,
            source=MemorySource.TASK_RESULT,
            metadata=metadata or {},
            explanation=f"Checkpoint at stage '{stage}', step {step_index}",
        )
        return self.store.save(item)

    def get_checkpoint(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves the latest checkpoint for a task."""
        item = self.store.get_by_key(
            category=MemoryCategory.TASK,
            key=f"checkpoint_{task_id}",
            scope=MemoryScope.TASK,
            scope_id=task_id,
        )
        return item.value if item else None

    def list_checkpoints(self) -> List[MemoryItem]:
        """Lists all existing task checkpoints."""
        return self.store.query(
            category=MemoryCategory.TASK,
            scope=MemoryScope.TASK,
        )

    def clear_checkpoint(self, task_id: str) -> bool:
        """Removes the checkpoint for a completed task."""
        count = self.store.delete_by_key(
            category=MemoryCategory.TASK,
            key=f"checkpoint_{task_id}",
            scope=MemoryScope.TASK,
            scope_id=task_id,
        )
        return count > 0
