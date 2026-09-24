"""
SHIVANI Project Context Engine (Phase 16).
Maintains active project context, generates structured context snapshots,
supports seamless project continuity across days/sessions,
and enforces cross-project file isolation and safety.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

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

logger = logging.getLogger("shivani.productivity.context_engine")


class ContextEngine:
    """Manages active project context, continuity across sessions, and boundary safety."""

    def __init__(self, store: ProductivityStore):
        self.store = store
        self._active_project_id: Optional[str] = None

    @property
    def active_project_id(self) -> Optional[str]:
        return self._active_project_id

    def set_active_project(self, project_id_or_name: str) -> Optional[Project]:
        """Switches active project context by ID or case-insensitive name."""
        project = self.store.get_project(project_id_or_name)
        if not project:
            project = self.store.get_project_by_name(project_id_or_name)

        if project:
            self._active_project_id = project.id
            logger.info(f"Switched active project context to '{project.name}' (ID: {project.id})")
            return project
        return None

    def get_active_project(self) -> Optional[Project]:
        if self._active_project_id:
            return self.store.get_project(self._active_project_id)
        return None

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        """
        Assembles a comprehensive, factual context snapshot for a project.
        """
        project = self.store.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        tasks = self.store.list_tasks(project_id=project_id)
        milestones = self.store.list_milestones(project_id=project_id)
        decisions = self.store.list_decisions(project_id=project_id)
        blockers = self.store.list_blockers(project_id=project_id, status="OPEN")

        open_tasks = [t for t in tasks if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]

        active_milestone = None
        for m in milestones:
            if m.status in (MilestoneStatus.IN_PROGRESS, MilestoneStatus.NOT_STARTED):
                active_milestone = m
                break

        # Check for stale context (> 30 days)
        is_stale = False
        days_since_update = 0
        try:
            up_dt = datetime.fromisoformat(project.updated_at.replace("Z", "+00:00"))
            if up_dt.tzinfo is None:
                up_dt = up_dt.replace(tzinfo=timezone.utc)
            days_since_update = (datetime.now(timezone.utc) - up_dt).days
            if days_since_update > 30:
                is_stale = True
        except Exception:
            pass

        return {
            "project_id": project.id,
            "project_name": project.name,
            "description": project.description,
            "status": project.status.value,
            "owner": project.owner,
            "codebase_path": project.codebase_path,
            "repo_url": project.repo_url,
            "active_milestone": active_milestone.title if active_milestone else "None",
            "milestones_count": len(milestones),
            "completed_milestones": sum(1 for m in milestones if m.status == MilestoneStatus.COMPLETED),
            "open_tasks_count": len(open_tasks),
            "blocked_tasks_count": len(blocked_tasks),
            "completed_tasks_count": len(completed_tasks),
            "recent_decisions": [
                {"topic": d.topic, "decision": d.decision, "date": d.date}
                for d in decisions[:5]
            ],
            "open_blockers": [
                {"title": b.title, "description": b.description, "affected_tasks": b.affected_tasks}
                for b in blockers
            ],
            "is_stale": is_stale,
            "days_since_update": days_since_update,
            "updated_at": project.updated_at,
        }

    def get_continuity_summary(self, project_id_or_name: str) -> Dict[str, Any]:
        """
        Supports: 'Continue my OCR project'
        Identifies current milestone, unfinished tasks, last known state, and blockers.
        """
        project = self.store.get_project(project_id_or_name)
        if not project:
            project = self.store.get_project_by_name(project_id_or_name)

        if not project:
            return {"found": False, "message": f"No project matching '{project_id_or_name}' exists."}

        self._active_project_id = project.id
        ctx = self.get_project_context(project.id)
        tasks = self.store.list_tasks(project_id=project.id)
        unfinished_tasks = [t for t in tasks if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED)]

        summary = (
            f"The '{project.name}' project was last active on {project.updated_at[:10]}. "
            f"The current milestone is '{ctx.get('active_milestone')}', with "
            f"{len(unfinished_tasks)} unfinished task(s) and {ctx.get('blocked_tasks_count')} blocker(s)."
        )

        return {
            "found": True,
            "project_id": project.id,
            "project_name": project.name,
            "summary_message": summary,
            "current_milestone": ctx.get("active_milestone"),
            "unfinished_tasks": [
                {"id": t.id, "title": t.title, "status": t.status.value, "priority": t.priority.value, "due_date": t.due_date}
                for t in unfinished_tasks[:5]
            ],
            "open_blockers": ctx.get("open_blockers"),
            "context": ctx,
        }

    def verify_project_file_boundary(
        self,
        target_path: str,
        project_id: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Safety check: Ensures actions targeting local codebases remain strictly
        confined within the declared codebase path of the active/target project.
        """
        pid = project_id or self._active_project_id
        if not pid:
            # No project context set, cannot enforce project path confinement
            return True, "No active project context"

        project = self.store.get_project(pid)
        if not project or not project.codebase_path:
            return True, "Project has no declared codebase path"

        try:
            base_p = Path(project.codebase_path).resolve()
            tgt_p = Path(target_path).resolve()
            if not str(tgt_p).startswith(str(base_p)):
                return False, (
                    f"Cross-project safety violation: Target path '{target_path}' is outside "
                    f"project '{project.name}' root directory ('{project.codebase_path}')."
                )
            return True, "Path is within project codebase"
        except Exception as e:
            return False, f"Path evaluation error: {e}"
