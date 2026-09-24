"""
SHIVANI Multi-Factor Priority Engine (Phase 16).
Provides structured, transparent priority scoring with explicit causal explanations.
Never claims objective omniscience—evaluates based on explicit criteria and user preferences.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from core.productivity.models import PersonalTask, PriorityScore, Project, TaskPriority, TaskStatus


class PriorityEngine:
    """Calculates multi-dimensional priority scores and provides clear reasoning."""

    DEFAULT_PREFERENCES = {
        "deadline_sensitivity": 1.0,     # Weight for deadline proximity
        "project_importance": 1.0,       # Weight for parent project priority
        "dependency_weight": 1.2,        # Weight for unblocking downstream tasks
        "prefer_short_tasks": False,     # Preference for quick wins (< 30m)
        "prefer_deep_work": True,        # Preference for deep work (> 60m)
    }

    def __init__(self, preferences: Optional[Dict[str, Any]] = None):
        self.preferences = dict(self.DEFAULT_PREFERENCES)
        if preferences:
            self.preferences.update(preferences)

    def evaluate_task(
        self,
        task: PersonalTask,
        all_tasks: List[PersonalTask],
        project: Optional[Project] = None,
    ) -> PriorityScore:
        factors: Dict[str, float] = {}
        reasons: List[str] = []

        # 1. Base Task Priority
        priority_weights = {
            TaskPriority.LOW: 1.0,
            TaskPriority.MEDIUM: 2.0,
            TaskPriority.HIGH: 3.5,
            TaskPriority.CRITICAL: 5.0,
        }
        base_weight = priority_weights.get(task.priority, 2.0)
        factors["base_priority"] = base_weight
        if task.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL):
            reasons.append(f"Marked as {task.priority.value} priority")

        # 2. Deadline Proximity
        deadline_score = 0.0
        if task.due_date:
            try:
                # Support YYYY-MM-DD or ISO
                due_dt = datetime.fromisoformat(task.due_date.replace("Z", "+00:00"))
                if due_dt.tzinfo is None:
                    due_dt = due_dt.replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_left = (due_dt - now).total_seconds() / 86400.0

                if days_left < 0:
                    deadline_score = 5.0  # Overdue
                    reasons.append("Task is OVERDUE")
                elif days_left <= 1.0:
                    deadline_score = 4.0  # Due today / within 24h
                    reasons.append("Deadline is approaching (due within 24 hours)")
                elif days_left <= 3.0:
                    deadline_score = 2.5  # Due soon
                    reasons.append("Due within 3 days")
                elif days_left <= 7.0:
                    deadline_score = 1.5
                    reasons.append("Due this week")
                else:
                    deadline_score = 0.5
            except Exception:
                deadline_score = 0.0
        factors["deadline_proximity"] = deadline_score * self.preferences["deadline_sensitivity"]

        # 3. Dependency Impact (How many other tasks does this task unblock?)
        unblocked_count = sum(1 for t in all_tasks if task.id in t.dependencies and t.status != TaskStatus.COMPLETED)
        if unblocked_count > 0:
            dep_score = min(unblocked_count * 1.5, 4.5) * self.preferences["dependency_weight"]
            factors["dependency_impact"] = dep_score
            reasons.append(f"Blocks {unblocked_count} other pending task(s)")
        else:
            factors["dependency_impact"] = 0.0

        # 4. Project Priority & Context
        proj_score = 0.0
        if project:
            if project.priority == TaskPriority.CRITICAL:
                proj_score = 3.0
                reasons.append(f"Part of critical project '{project.name}'")
            elif project.priority == TaskPriority.HIGH:
                proj_score = 2.0
                reasons.append(f"Part of high-priority project '{project.name}'")
            else:
                proj_score = 1.0
        factors["project_priority"] = proj_score * self.preferences["project_importance"]

        # 5. Effort & Duration Preference
        effort_score = 0.0
        if self.preferences.get("prefer_short_tasks") and task.estimated_duration_minutes <= 30:
            effort_score = 1.0
            reasons.append("Matches preference for short, focused tasks")
        elif self.preferences.get("prefer_deep_work") and task.estimated_duration_minutes >= 60:
            effort_score = 1.0
            reasons.append("Matches preference for deep work blocks")
        factors["effort_preference"] = effort_score

        # 6. Blocked Penalty
        # If task itself is blocked, reduce immediate actionability
        is_blocked = task.status == TaskStatus.BLOCKED
        if is_blocked:
            factors["blocked_penalty"] = -10.0
            reasons.append("Currently marked as BLOCKED")

        total_score = sum(factors.values())
        return PriorityScore(
            task_id=task.id,
            total_score=round(total_score, 2),
            factors=factors,
            reasons=reasons or ["Standard priority scheduling"],
        )

    def rank_tasks(
        self,
        tasks: List[PersonalTask],
        all_tasks: Optional[List[PersonalTask]] = None,
        projects_map: Optional[Dict[str, Project]] = None,
    ) -> List[Tuple[PersonalTask, PriorityScore]]:
        """Ranks tasks in descending order of calculated priority score."""
        pool = all_tasks or tasks
        p_map = projects_map or {}
        scored = []
        for t in tasks:
            proj = p_map.get(t.project_id) if t.project_id else None
            score = self.evaluate_task(t, pool, proj)
            scored.append((t, score))

        scored.sort(key=lambda item: item[1].total_score, reverse=True)
        return scored
