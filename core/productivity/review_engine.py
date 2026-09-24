"""
SHIVANI Review & Retrospective Engine (Phase 16).
Generates factual weekly and monthly reviews and structured project retrospectives.
Avoids judgmental psychological scores; focuses strictly on deliverables and blockers.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from core.productivity.models import (
    Blocker,
    Decision,
    Milestone,
    MilestoneStatus,
    PersonalTask,
    Project,
    TaskStatus,
)
from core.productivity.store import ProductivityStore


class ReviewEngine:
    """Produces objective, retrospective reports over weeks, months, or project lifecycles."""

    def __init__(self, store: ProductivityStore):
        self.store = store

    def generate_weekly_review(self, now: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Summarizes deliverables and challenges over the past 7 days.
        """
        ref_now = now or datetime.now(timezone.utc)
        week_ago = ref_now - timedelta(days=7)
        week_ago_iso = week_ago.isoformat()

        all_tasks = self.store.list_tasks()
        all_projects = self.store.list_projects()
        all_blockers = self.store.list_blockers()
        all_decisions = self.store.list_decisions()

        # 1. Completed Tasks in past 7 days
        completed_recently: List[PersonalTask] = []
        for t in all_tasks:
            if t.status == TaskStatus.COMPLETED and t.completed_at and t.completed_at >= week_ago_iso:
                completed_recently.append(t)
            elif t.status == TaskStatus.COMPLETED and not t.completed_at:
                completed_recently.append(t)

        # 2. Blocked & Overdue
        blocked_tasks = [t for t in all_tasks if t.status == TaskStatus.BLOCKED]
        overdue_tasks = []
        for t in all_tasks:
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED) and t.due_date:
                try:
                    due_dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    if due_dt.tzinfo is None:
                        due_dt = due_dt.replace(tzinfo=timezone.utc)
                    if due_dt < ref_now:
                        overdue_tasks.append(t)
                except Exception:
                    pass

        # 3. Projects Advanced
        active_project_ids = {t.project_id for t in completed_recently if t.project_id}
        projects_advanced = [p.name for p in all_projects if p.id in active_project_ids]

        # 4. Open Blockers
        open_blockers = [b for b in all_blockers if b.status == "OPEN"]

        # 5. Recent Decisions
        recent_decisions = [d for d in all_decisions if d.created_at >= week_ago_iso]

        return {
            "period": "Past 7 Days",
            "completed_tasks_count": len(completed_recently),
            "completed_tasks": [{"id": t.id, "title": t.title, "project_id": t.project_id} for t in completed_recently[:10]],
            "projects_advanced_count": len(projects_advanced),
            "projects_advanced": projects_advanced,
            "blocked_tasks_count": len(blocked_tasks),
            "blocked_tasks": [{"id": t.id, "title": t.title} for t in blocked_tasks[:5]],
            "overdue_tasks_count": len(overdue_tasks),
            "overdue_tasks": [{"id": t.id, "title": t.title, "due_date": t.due_date} for t in overdue_tasks[:5]],
            "open_blockers_count": len(open_blockers),
            "recent_decisions_count": len(recent_decisions),
            "recent_decisions": [{"topic": d.topic, "decision": d.decision} for d in recent_decisions[:5]],
        }

    def generate_project_retrospective(self, project_id: str) -> Dict[str, Any]:
        """
        Generates a comprehensive retrospective for a specific project.
        """
        project = self.store.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        tasks = self.store.list_tasks(project_id=project_id)
        milestones = self.store.list_milestones(project_id=project_id)
        decisions = self.store.list_decisions(project_id=project_id)
        blockers = self.store.list_blockers(project_id=project_id)

        completed_milestones = [m for m in milestones if m.status == MilestoneStatus.COMPLETED]
        pending_milestones = [m for m in milestones if m.status != MilestoneStatus.COMPLETED]
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        unresolved_blockers = [b for b in blockers if b.status == "OPEN"]
        resolved_blockers = [b for b in blockers if b.status == "RESOLVED"]

        return {
            "project_name": project.name,
            "project_status": project.status.value,
            "completed_milestones": [
                {"title": m.title, "target_date": m.target_date}
                for m in completed_milestones
            ],
            "pending_milestones": [
                {"title": m.title, "status": m.status.value, "progress": m.progress}
                for m in pending_milestones
            ],
            "total_tasks": len(tasks),
            "completed_tasks": len(completed_tasks),
            "major_decisions": [
                {"topic": d.topic, "decision": d.decision, "reason": d.reason, "date": d.date}
                for d in decisions
            ],
            "resolved_blockers": [
                {"title": b.title, "resolution": b.resolution}
                for b in resolved_blockers
            ],
            "unresolved_blockers": [
                {"title": b.title, "description": b.description}
                for b in unresolved_blockers
            ],
        }
