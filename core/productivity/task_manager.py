"""
SHIVANI Task Manager (Phase 16).
Manages personal tasks, natural-language parsing, conversational references,
strict completion verification, task batching, and stale task detection.
"""

from datetime import datetime, timedelta, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from core.productivity.models import (
    PersonalTask,
    Project,
    TaskPriority,
    TaskStatus,
)
from core.productivity.store import ProductivityStore
from core.productivity.verification_gate import TaskCompletionGate

logger = logging.getLogger("shivani.productivity.task_manager")


class TaskManager:
    """Coordinates task creation, conversational updates, verification, and batching."""

    def __init__(self, store: ProductivityStore):
        self.store = store
        self._last_referenced_task_id: Optional[str] = None

    @property
    def last_referenced_task_id(self) -> Optional[str]:
        return self._last_referenced_task_id

    def set_referenced_task(self, task_id: str) -> None:
        self._last_referenced_task_id = task_id

    def create_task(
        self,
        title: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        project_id: Optional[str] = None,
        goal_id: Optional[str] = None,
        milestone_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
        due_date: Optional[str] = None,
        estimated_duration_minutes: int = 30,
        tags: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        artifacts: Optional[List[str]] = None,
    ) -> PersonalTask:
        task = PersonalTask(
            title=title,
            description=description,
            priority=priority,
            project_id=project_id,
            goal_id=goal_id,
            milestone_id=milestone_id,
            dependencies=dependencies or [],
            due_date=due_date,
            estimated_duration_minutes=estimated_duration_minutes,
            tags=tags or [],
            context=context or {},
            artifacts=artifacts or [],
        )
        self.store.save_task(task)
        self._last_referenced_task_id = task.id
        logger.info(f"Created task '{task.title}' (ID: {task.id})")
        return task

    def parse_natural_language_task(
        self,
        prompt: str,
        active_project_id: Optional[str] = None,
    ) -> PersonalTask:
        """
        Parses prompts such as:
        'Remind me to finish the README tomorrow'
        'Add testing as the next task for the OCR project'
        """
        text = prompt.strip()

        # 1. Detect relative due dates
        due_date = None
        now_dt = datetime.now(timezone.utc)
        if re.search(r"\btomorrow\b", text, re.IGNORECASE):
            due_date = (now_dt + timedelta(days=1)).strftime("%Y-%m-%d")
        elif re.search(r"\btoday\b", text, re.IGNORECASE):
            due_date = now_dt.strftime("%Y-%m-%d")
        elif re.search(r"\bnext week\b", text, re.IGNORECASE):
            due_date = (now_dt + timedelta(days=7)).strftime("%Y-%m-%d")

        # 2. Detect Priority
        priority = TaskPriority.MEDIUM
        if re.search(r"\b(urgent|critical|asap)\b", text, re.IGNORECASE):
            priority = TaskPriority.CRITICAL
        elif re.search(r"\b(high priority|important)\b", text, re.IGNORECASE):
            priority = TaskPriority.HIGH
        elif re.search(r"\b(low priority|someday)\b", text, re.IGNORECASE):
            priority = TaskPriority.LOW

        # 3. Detect Project association
        project_id = active_project_id
        for p in self.store.list_projects():
            if re.search(rf"\b{re.escape(p.name)}\b", text, re.IGNORECASE):
                project_id = p.id
                break

        # 4. Clean title
        clean_title = re.sub(
            r"^(remind me to|add task|create task|add|todo:?)\s+",
            "",
            text,
            flags=re.IGNORECASE,
        ).strip()
        # Strip trailing due date mentions
        clean_title = re.sub(
            r"\s+(tomorrow|today|next week|by friday)$",
            "",
            clean_title,
            flags=re.IGNORECASE,
        ).strip()
        # Strip trailing project mentions
        clean_title = re.sub(
            r"\s+(for|in|under)\s+(the\s+)?(project\s+)?[a-zA-Z0-9_\-\s]+$",
            "",
            clean_title,
            flags=re.IGNORECASE,
        ).strip()

        if not clean_title:
            clean_title = prompt.strip()

        return self.create_task(
            title=clean_title.capitalize(),
            priority=priority,
            project_id=project_id,
            due_date=due_date,
        )

    def resolve_conversational_reference(
        self,
        query: str,
        active_project_id: Optional[str] = None,
    ) -> Tuple[Optional[PersonalTask], str]:
        """
        Resolves references such as:
        'Mark that as done'
        'Move it to tomorrow'
        'Put this under the Shivani project'
        """
        task_id = self._last_referenced_task_id
        if not task_id:
            # Fall back to most recently modified task in active project or globally
            recent = self.store.list_tasks(project_id=active_project_id)
            if recent:
                task_id = recent[0].id

        if not task_id:
            return None, "No active or recent task found to reference."

        task = self.store.get_task(task_id)
        if not task:
            return None, f"Referenced task '{task_id}' no longer exists."

        # Process directives
        q_lower = query.lower()

        if any(w in q_lower for w in ["done", "complete", "finished"]):
            verified, errors = self.complete_task(task.id, execution_output={"manually_confirmed": True})
            if verified:
                return task, f"Marked task '{task.title}' as COMPLETED."
            else:
                return task, f"Could not complete task '{task.title}': {'; '.join(errors)}"

        elif "tomorrow" in q_lower:
            new_date = (datetime.now(timezone.utc) + timedelta(days=1)).strftime("%Y-%m-%d")
            task.due_date = new_date
            self.store.save_task(task)
            return task, f"Rescheduled task '{task.title}' to tomorrow ({new_date})."

        elif "under" in q_lower or "project" in q_lower:
            for p in self.store.list_projects():
                if p.name.lower() in q_lower:
                    task.project_id = p.id
                    self.store.save_task(task)
                    return task, f"Moved task '{task.title}' under project '{p.name}'."

        return task, f"Referenced task is '{task.title}'."

    def complete_task(
        self,
        task_id: str,
        execution_output: Optional[Dict[str, Any]] = None,
        skip_verification: bool = False,
    ) -> Tuple[bool, List[str]]:
        """
        Transitions task to COMPLETED through the TaskCompletionGate.
        """
        task = self.store.get_task(task_id)
        if not task:
            return False, [f"Task '{task_id}' not found"]

        if not skip_verification:
            verified, failures = TaskCompletionGate.verify_completion(task, execution_output)
            if not verified:
                logger.warning(f"Task '{task.title}' failed completion gate: {failures}")
                return False, failures

        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now(timezone.utc).isoformat()
        if execution_output and "artifact_path" in execution_output:
            task.artifacts.append(str(execution_output["artifact_path"]))

        self.store.save_task(task)
        self._last_referenced_task_id = task.id
        logger.info(f"Verified and completed task '{task.title}'")
        return True, []

    def find_batchable_tasks(
        self,
        project_id: Optional[str] = None,
        max_duration_minutes: int = 45,
    ) -> List[PersonalTask]:
        """
        Identifies small compatible tasks (<= 30 min) that can be batched together.
        """
        tasks = self.store.list_tasks(project_id=project_id, status="TODO")
        batchable = [
            t for t in tasks
            if t.estimated_duration_minutes <= 30
            and not t.dependencies
        ]
        return batchable[:5]

    def detect_stale_tasks(self, days_threshold: int = 10) -> List[PersonalTask]:
        """
        Finds open tasks that have had no updates or activity for > days_threshold.
        """
        tasks = self.store.list_tasks()
        now = datetime.now(timezone.utc)
        stale: List[PersonalTask] = []

        for t in tasks:
            if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED):
                try:
                    up_dt = datetime.fromisoformat(t.updated_at.replace("Z", "+00:00"))
                    if up_dt.tzinfo is None:
                        up_dt = up_dt.replace(tzinfo=timezone.utc)
                    if (now - up_dt).days >= days_threshold:
                        stale.append(t)
                except Exception:
                    pass

        return stale
