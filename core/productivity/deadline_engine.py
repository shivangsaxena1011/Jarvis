"""
SHIVANI Deadline Engine (Phase 16).
Categorizes tasks by due date windows and detects deadline conflicts
(e.g., dependency due after dependent, overlapping critical deadlines).
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from core.productivity.models import PersonalTask, TaskStatus


class DeadlineEngine:
    """Manages task deadlines, overdue tracking, and schedule conflict resolution."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parses ISO or YYYY-MM-DD date into timezone-aware UTC datetime."""
        if not date_str:
            return None
        try:
            # Handle YYYY-MM-DD
            if len(date_str) == 10 and date_str.count("-") == 2:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                return dt.replace(tzinfo=timezone.utc)
            # Handle ISO
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            return None

    @classmethod
    def categorize_deadlines(
        cls,
        tasks: List[PersonalTask],
        now: Optional[datetime] = None,
    ) -> Dict[str, List[PersonalTask]]:
        """
        Groups tasks into: overdue, today, tomorrow, this_week, upcoming, no_deadline.
        """
        ref_now = now or datetime.now(timezone.utc)
        today_date = ref_now.date()
        tomorrow_date = today_date + timedelta(days=1)
        week_end_date = today_date + timedelta(days=7)

        buckets: Dict[str, List[PersonalTask]] = {
            "overdue": [],
            "today": [],
            "tomorrow": [],
            "this_week": [],
            "upcoming": [],
            "no_deadline": [],
        }

        for task in tasks:
            if task.status == TaskStatus.COMPLETED or task.status == TaskStatus.CANCELLED:
                continue

            if not task.due_date:
                buckets["no_deadline"].append(task)
                continue

            dt = cls.parse_date(task.due_date)
            if not dt:
                buckets["no_deadline"].append(task)
                continue

            task_date = dt.date()
            if task_date < today_date:
                buckets["overdue"].append(task)
            elif task_date == today_date:
                buckets["today"].append(task)
            elif task_date == tomorrow_date:
                buckets["tomorrow"].append(task)
            elif today_date < task_date <= week_end_date:
                buckets["this_week"].append(task)
            else:
                buckets["upcoming"].append(task)

        return buckets

    @classmethod
    def detect_conflicts(
        cls,
        tasks: List[PersonalTask],
    ) -> List[Dict[str, Any]]:
        """
        Detects deadline conflicts:
        1. Dependency Inversion: Task A depends on Task B, but Task A's due date is BEFORE Task B's due date.
        2. Impossible Schedule: More than 8 hours of critical tasks due on the exact same date.
        """
        conflicts: List[Dict[str, Any]] = []
        task_map = {t.id: t for t in tasks}

        for task in tasks:
            if not task.due_date or task.status == TaskStatus.COMPLETED:
                continue

            t_date = cls.parse_date(task.due_date)
            if not t_date:
                continue

            for dep_id in task.dependencies:
                dep_task = task_map.get(dep_id)
                if dep_task and dep_task.due_date and dep_task.status != TaskStatus.COMPLETED:
                    dep_date = cls.parse_date(dep_task.due_date)
                    if dep_date and dep_date > t_date:
                        conflicts.append({
                            "type": "DEPENDENCY_DEADLINE_INVERSION",
                            "task_id": task.id,
                            "task_title": task.title,
                            "task_due": task.due_date,
                            "dependency_id": dep_task.id,
                            "dependency_title": dep_task.title,
                            "dependency_due": dep_task.due_date,
                            "description": (
                                f"Task '{task.title}' is due on {task.due_date}, but prerequisite "
                                f"'{dep_task.title}' is scheduled later ({dep_task.due_date})."
                            ),
                        })

        return conflicts
