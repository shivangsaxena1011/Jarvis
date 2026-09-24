"""
SHIVANI Task Checkpoint & Safe Resume Engine (Phase 17).
Provides state checkpointing, rollback tracking, and non-destructive
task resumption based on current observed state rather than blind replay.
"""

from __future__ import annotations
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from core.computer.models import ApplicationContext, TaskCheckpoint


class CheckpointEngine:
    """Manages long-horizon computer task checkpoints and rollback trails."""

    def __init__(self, checkpoints_dir: Optional[str] = None):
        self.checkpoints_dir = Path(checkpoints_dir or "data/computer/checkpoints")
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.rollback_stack: List[Dict[str, Any]] = []

    def create_checkpoint(
        self,
        task_id: str,
        step_index: int,
        app_context: ApplicationContext,
        completed_actions: List[Dict[str, Any]],
        pending_steps: List[str],
        modified_files: Optional[List[str]] = None,
        summary: str = "",
    ) -> TaskCheckpoint:
        """
        Creates and persists a task checkpoint to disk.
        """
        ckpt = TaskCheckpoint(
            task_id=task_id,
            step_index=step_index,
            timestamp=time.time(),
            app_context=app_context,
            completed_actions=list(completed_actions),
            modified_files=list(modified_files or []),
            pending_steps=list(pending_steps),
            summary=summary,
        )

        task_dir = self.checkpoints_dir / task_id
        task_dir.mkdir(parents=True, exist_ok=True)
        ckpt_file = task_dir / f"step_{step_index:03d}_{ckpt.checkpoint_id}.json"
        ckpt_file.write_text(ckpt.model_dump_json(indent=2), encoding="utf-8")
        return ckpt

    def get_latest_checkpoint(self, task_id: str) -> Optional[TaskCheckpoint]:
        """Loads the most recent checkpoint for a given task ID."""
        task_dir = self.checkpoints_dir / task_id
        if not task_dir.exists():
            return None

        files = sorted(task_dir.glob("step_*.json"), reverse=True)
        if not files:
            return None

        try:
            content = files[0].read_text(encoding="utf-8")
            data = json.loads(content)
            return TaskCheckpoint(**data)
        except Exception:
            return None

    def record_rollback_action(self, action_type: str, details: Dict[str, Any]):
        """
        Pushes a compensating action to the rollback stack.
        E.g. ('file_move', {'from': dest, 'to': src}), ('file_create', {'path': p})
        """
        self.rollback_stack.append({
            "action_type": action_type,
            "details": details,
            "timestamp": time.time(),
        })

    def execute_rollback(self) -> List[Dict[str, Any]]:
        """
        Executes recorded rollback actions in LIFO order.
        """
        results = []
        while self.rollback_stack:
            item = self.rollback_stack.pop()
            atype = item["action_type"]
            det = item["details"]
            res = {"action_type": atype, "success": False}

            try:
                if atype == "file_move":
                    src = Path(det["from"])
                    dst = Path(det["to"])
                    if src.exists():
                        shutil.move(str(src), str(dst))
                        res["success"] = True
                elif atype == "file_create":
                    p = Path(det["path"])
                    if p.exists():
                        p.unlink()
                        res["success"] = True
                elif atype == "dir_create":
                    p = Path(det["path"])
                    if p.exists() and not any(p.iterdir()):
                        p.rmdir()
                        res["success"] = True
            except Exception as e:
                res["error"] = str(e)

            results.append(res)
        return results

    def plan_safe_resume(
        self,
        checkpoint: TaskCheckpoint,
        current_app_context: ApplicationContext,
        existing_artifacts: List[str],
    ) -> List[str]:
        """
        Determines remaining steps by verifying what has already succeeded
        in current reality, avoiding redundant replays.
        """
        remaining: List[str] = []
        for step in checkpoint.pending_steps:
            # If the step was to create an artifact and the artifact already exists, skip it
            already_done = any(art.lower() in step.lower() for art in existing_artifacts)
            if not already_done:
                remaining.append(step)
        return remaining
