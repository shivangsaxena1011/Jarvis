"""
SHIVANI Planning Engine (Phase 16).
Generates realistic, time-aware daily schedules and weekly reviews.
Warns on time overload, supports user approval before locking schedules,
and respects working hours and focus preferences.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple

from core.productivity.models import (
    DailyPlan,
    PersonalTask,
    PlanStatus,
    PriorityScore,
    Project,
    TaskPriority,
    TaskStatus,
    TimeBlock,
)
from core.productivity.priority_engine import PriorityEngine
from core.productivity.store import ProductivityStore

logger = logging.getLogger("shivani.productivity.planning_engine")


class PlanningEngine:
    """Produces proposed daily schedules and verifies capacity against commitments."""

    def __init__(self, store: ProductivityStore, priority_engine: PriorityEngine):
        self.store = store
        self.priority_engine = priority_engine

    def generate_daily_plan(
        self,
        date_str: Optional[str] = None,
        available_minutes: int = 480,  # 8 hours default
        start_hour: int = 9,
    ) -> Tuple[DailyPlan, Optional[str]]:
        """
        Creates a proposed daily schedule based on tasks, deadlines, and priorities.
        Returns (DailyPlan, optional_capacity_warning).
        """
        target_date = date_str or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # 1. Fetch actionable tasks (TODO, IN_PROGRESS)
        all_tasks = self.store.list_tasks()
        actionable_tasks = [
            t for t in all_tasks
            if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)
        ]

        projects = {p.id: p for p in self.store.list_projects()}

        # 2. Rank tasks using PriorityEngine
        ranked = self.priority_engine.rank_tasks(actionable_tasks, all_tasks, projects)

        # 3. Time Capacity Check & Allocation
        time_blocks: List[TimeBlock] = []
        current_minute = start_hour * 60  # e.g., 09:00 -> 540 min
        total_planned_minutes = 0

        # Calculate total demanded minutes across all actionable tasks
        total_demanded_minutes = sum(t.estimated_duration_minutes for t, _ in ranked)
        warning_msg: Optional[str] = None
        if total_demanded_minutes > available_minutes:
            diff_hours = round((total_demanded_minutes - available_minutes) / 60, 1)
            warning_msg = (
                f"Schedule Overload: There are {round(total_demanded_minutes / 60, 1)} hours of "
                f"work requested, but only {round(available_minutes / 60, 1)} available hours today "
                f"({diff_hours}h surplus). The proposed plan selects only top-ranked tasks."
            )

        for task, score in ranked:
            est = max(task.estimated_duration_minutes, 15)
            if total_planned_minutes + est > available_minutes:
                # Reached available time budget
                continue

            start_h, start_m = divmod(current_minute, 60)
            end_minute = current_minute + est
            end_h, end_m = divmod(end_minute, 60)

            time_blocks.append(
                TimeBlock(
                    start_time=f"{start_h:02d}:{start_m:02d}",
                    end_time=f"{end_h:02d}:{end_m:02d}",
                    task_id=task.id,
                    title=task.title,
                    category="Deep Work" if est >= 60 else "Focused Task",
                    description=f"Priority: {score.total_score} | Reasons: {', '.join(score.reasons[:2])}",
                )
            )

            current_minute = end_minute
            total_planned_minutes += est

            # Add short 15m break after deep work blocks
            if est >= 60 and (total_planned_minutes + 15 <= available_minutes):
                b_start_h, b_start_m = divmod(current_minute, 60)
                current_minute += 15
                total_planned_minutes += 15
                b_end_h, b_end_m = divmod(current_minute, 60)
                time_blocks.append(
                    TimeBlock(
                        start_time=f"{b_start_h:02d}:{b_start_m:02d}",
                        end_time=f"{b_end_h:02d}:{b_end_m:02d}",
                        task_id=None,
                        title="Buffer & Rest Break",
                        category="Break",
                        description="Rest and cognitive reset",
                    )
                )

        plan = DailyPlan(
            date=target_date,
            time_blocks=time_blocks,
            status=PlanStatus.PROPOSED,
            total_planned_minutes=total_planned_minutes,
            available_minutes=available_minutes,
            notes=warning_msg or "Proposed schedule ready for review.",
        )

        self.store.save_daily_plan(plan)
        return plan, warning_msg

    def accept_plan(self, plan_id: str) -> bool:
        """User explicitly accepts the proposed daily plan."""
        plans = self.store.list_daily_plans(limit=10)
        for p in plans:
            if p.id == plan_id:
                p.status = PlanStatus.ACCEPTED
                self.store.save_daily_plan(p)
                return True
        return False
