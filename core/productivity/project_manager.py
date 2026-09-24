"""
SHIVANI Project Manager (Phase 16).
Manages software and creative projects, architectural decisions,
requirements tracking, blocker management, and factual project health.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from core.productivity.models import (
    Blocker,
    BlockerStatus,
    Decision,
    DecisionStatus,
    Milestone,
    MilestoneStatus,
    PersonalTask,
    Project,
    ProjectStatus,
    Requirement,
    RequirementStatus,
    TaskPriority,
    TaskStatus,
)
from core.productivity.store import ProductivityStore

logger = logging.getLogger("shivani.productivity.project_manager")


class ProjectManager:
    """Manages the full lifecycle of projects, decisions, requirements, and blockers."""

    def __init__(self, store: ProductivityStore):
        self.store = store

    def create_project(
        self,
        name: str,
        description: str = "",
        priority: TaskPriority = TaskPriority.MEDIUM,
        codebase_path: Optional[str] = None,
        repo_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Project:
        project = Project(
            name=name,
            description=description,
            priority=priority,
            codebase_path=codebase_path,
            repo_url=repo_url,
            tags=tags or [],
        )
        self.store.save_project(project)
        logger.info(f"Created project '{project.name}' (ID: {project.id})")
        return project

    def get_project(self, project_id: str) -> Optional[Project]:
        return self.store.get_project(project_id)

    def get_project_by_name(self, name: str) -> Optional[Project]:
        return self.store.get_project_by_name(name)

    def list_projects(self, status: Optional[str] = None) -> List[Project]:
        return self.store.list_projects(status=status)

    def get_project_health(self, project_id: str) -> Dict[str, Any]:
        """
        Computes factual project health metrics without arbitrary scoring.
        """
        project = self.store.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        tasks = self.store.list_tasks(project_id=project_id)
        milestones = self.store.list_milestones(project_id=project_id)
        blockers = self.store.list_blockers(project_id=project_id, status="OPEN")

        open_tasks = [t for t in tasks if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
        blocked_tasks = [t for t in tasks if t.status == TaskStatus.BLOCKED]
        overdue_tasks = []
        now = datetime.now(timezone.utc)
        for t in tasks:
            if t.status not in (TaskStatus.COMPLETED, TaskStatus.CANCELLED) and t.due_date:
                try:
                    dt = datetime.fromisoformat(t.due_date.replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    if dt < now:
                        overdue_tasks.append(t)
                except Exception:
                    pass

        active_milestone = None
        for m in milestones:
            if m.status in (MilestoneStatus.IN_PROGRESS, MilestoneStatus.NOT_STARTED):
                active_milestone = m
                break

        needs_attention: List[str] = []
        if blockers:
            needs_attention.append(f"{len(blockers)} unresolved blocker(s)")
        if overdue_tasks:
            needs_attention.append(f"{len(overdue_tasks)} overdue task(s)")
        if blocked_tasks:
            needs_attention.append(f"{len(blocked_tasks)} blocked task(s)")

        return {
            "project_name": project.name,
            "status": project.status.value,
            "open_tasks": len(open_tasks),
            "blocked_tasks": len(blocked_tasks),
            "overdue_tasks": len(overdue_tasks),
            "open_blockers": len(blockers),
            "active_milestone": active_milestone.title if active_milestone else "None",
            "milestone_progress": f"{sum(1 for m in milestones if m.status == MilestoneStatus.COMPLETED)}/{len(milestones)} completed",
            "needs_attention": needs_attention,
            "is_healthy": len(needs_attention) == 0,
        }

    # ==========================================================================
    # DECISIONS
    # ==========================================================================

    def record_decision(
        self,
        project_id: str,
        topic: str,
        decision: str,
        reason: str,
    ) -> Decision:
        dec = Decision(
            project_id=project_id,
            topic=topic,
            decision=decision,
            reason=reason,
        )
        self.store.save_decision(dec)
        logger.info(f"Recorded decision on '{topic}' for project '{project_id}'")
        return dec

    def supersede_decision(self, old_decision_id: str, new_decision_id: str) -> bool:
        dec = self.store.get_decision(old_decision_id)
        if dec:
            dec.status = DecisionStatus.SUPERSEDED
            dec.superseded_by = new_decision_id
            self.store.save_decision(dec)
            return True
        return False

    # ==========================================================================
    # REQUIREMENTS
    # ==========================================================================

    def record_requirement(
        self,
        project_id: str,
        req_id: str,
        title: str,
        description: str = "",
        design: str = "",
        implementation: str = "",
        test_cases: Optional[List[str]] = None,
    ) -> Requirement:
        req = Requirement(
            project_id=project_id,
            req_id=req_id,
            title=title,
            description=description,
            design=design,
            implementation=implementation,
            test_cases=test_cases or [],
        )
        self.store.save_requirement(req)
        return req

    # ==========================================================================
    # BLOCKERS
    # ==========================================================================

    def record_blocker(
        self,
        project_id: str,
        title: str,
        description: str,
        affected_tasks: Optional[List[str]] = None,
        dependency: str = "",
    ) -> Blocker:
        blk = Blocker(
            project_id=project_id,
            title=title,
            description=description,
            affected_tasks=affected_tasks or [],
            dependency=dependency,
        )
        self.store.save_blocker(blk)

        # Automatically transition affected tasks to BLOCKED
        for tid in blk.affected_tasks:
            task = self.store.get_task(tid)
            if task and task.status != TaskStatus.COMPLETED:
                task.status = TaskStatus.BLOCKED
                self.store.save_task(task)

        return blk

    def resolve_blocker(self, blocker_id: str, resolution: str) -> Optional[Blocker]:
        blk = self.store.get_blocker(blocker_id)
        if not blk:
            return None

        blk.status = BlockerStatus.RESOLVED
        blk.resolution = resolution
        blk.resolved_at = datetime.now(timezone.utc).isoformat()
        self.store.save_blocker(blk)

        # Unblock affected tasks if they have no other blockers
        for tid in blk.affected_tasks:
            task = self.store.get_task(tid)
            if task and task.status == TaskStatus.BLOCKED:
                task.status = TaskStatus.TODO
                self.store.save_task(task)

        return blk
