"""
SHIVANI Task Checkpoint Manager
Persists execution state for long-running workflows across restarts,
crashes, power interruptions, and temporary network failures.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class TaskCheckpoint(BaseModel):
    task_id: str
    query: str = ""
    stage: str = "IN_PROGRESS"
    status: str = "IN_PROGRESS"  # IN_PROGRESS | PAUSED | RECOVERING | COMPLETED | FAILED
    current_step: int = 0
    step_index: int = 0
    total_steps: int = 0
    completed_steps: List[int] = Field(default_factory=list)
    failed_step: Optional[int] = None
    retry_count: int = 0
    step_outputs: Dict[str, Any] = Field(default_factory=dict)
    state: Dict[str, Any] = Field(default_factory=dict)
    idempotency_keys: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def __getitem__(self, item: str) -> Any:
        return getattr(self, item)


class CheckpointManager:
    def __init__(self, checkpoints_dir: Optional[str] = None, checkpoint_dir: Optional[str] = None):
        target_dir = checkpoint_dir or checkpoints_dir
        if target_dir:
            self.checkpoints_dir = Path(target_dir)
        else:
            base = Path(os.environ.get("APPDATA", Path.home() / ".config")) / "Shivani" / "tasks"
            self.checkpoints_dir = base
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _file_path(self, task_id: str) -> Path:
        safe_id = "".join(c for c in task_id if c.isalnum() or c in ("-", "_"))
        return self.checkpoints_dir / f"checkpoint_{safe_id}.json"

    def save_checkpoint(
        self,
        checkpoint: Optional[TaskCheckpoint] = None,
        task_id: Optional[str] = None,
        stage: str = "IN_PROGRESS",
        step_index: int = 0,
        total_steps: int = 0,
        state: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> TaskCheckpoint:
        if checkpoint is None:
            if not task_id:
                raise ValueError("task_id is required if checkpoint model not provided.")
            checkpoint = TaskCheckpoint(
                task_id=task_id,
                stage=stage,
                step_index=step_index,
                current_step=step_index,
                total_steps=total_steps,
                state=state or {},
                query=kwargs.get("query", ""),
                metadata=kwargs.get("metadata", {}),
            )
        checkpoint.updated_at = datetime.now(timezone.utc).isoformat()
        with self._lock:
            fp = self._file_path(checkpoint.task_id)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(checkpoint.model_dump_json(indent=2))
        return checkpoint

    def get_checkpoint(self, task_id: str) -> Optional[TaskCheckpoint]:
        with self._lock:
            fp = self._file_path(task_id)
            if not fp.exists():
                return None
            try:
                with open(fp, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return TaskCheckpoint.model_validate(data)
            except Exception:
                return None

    def list_interrupted_tasks(self) -> List[TaskCheckpoint]:
        """Detects in-progress or recovering tasks that were interrupted by application shutdown."""
        with self._lock:
            interrupted = []
            for fp in self.checkpoints_dir.glob("checkpoint_*.json"):
                try:
                    with open(fp, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    chk = TaskCheckpoint.model_validate(data)
                    if chk.status in ("IN_PROGRESS", "RECOVERING", "PAUSED"):
                        interrupted.append(chk)
                except Exception:
                    continue
            return interrupted

    def clear_checkpoint(self, task_id: str) -> bool:
        with self._lock:
            fp = self._file_path(task_id)
            if fp.exists():
                try:
                    fp.unlink()
                    return True
                except Exception:
                    return False
            return False
