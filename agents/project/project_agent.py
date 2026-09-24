"""
SHIVANI Project Agent (Phase 16).
Responsible for project context, task decomposition, milestone tracking,
continuity restoration, blocker root-cause analysis, and cross-agent coordination.
Subordinate to the Master Orchestrator; coordinates specialized agents.
"""

import logging
from typing import Any, Dict, List, Optional

from core.productivity.models import (
    Blocker,
    Milestone,
    PersonalTask,
    Project,
    TaskStatus,
)
from core.productivity.orchestrator import ProductivityOrchestrator

logger = logging.getLogger("shivani.agents.project")


class ProjectAgent:
    """Project Agent maintaining continuity, decomposition, and specialized agent coordination."""

    def __init__(self, productivity: ProductivityOrchestrator):
        self.prod = productivity

    def load_project_context(self, project_id_or_name: str) -> Dict[str, Any]:
        """Loads and returns active project context snapshot."""
        return self.prod.context.get_continuity_summary(project_id_or_name)

    def plan_project_milestones(self, project_id: str, goal_title: str) -> Dict[str, Any]:
        """Proposes structured milestones for a project."""
        return self.prod.goals.propose_goal_breakdown(goal_title, category="Project")

    def analyze_blockers(self, project_id: str) -> Dict[str, Any]:
        """Traces the dependency graph to analyze the root cause of blockers."""
        project = self.prod.projects.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}

        open_blockers = self.prod.store.list_blockers(project_id=project_id, status="OPEN")
        tasks = self.prod.store.list_tasks(project_id=project_id)
        task_map = {t.id: t for t in tasks}

        traced_blockers = []
        for b in open_blockers:
            affected = [task_map[tid].title for tid in b.affected_tasks if tid in task_map]
            traced_blockers.append({
                "blocker_id": b.id,
                "title": b.title,
                "description": b.description,
                "dependency": b.dependency,
                "affected_tasks": affected,
            })

        return {
            "project_name": project.name,
            "open_blockers_count": len(open_blockers),
            "blockers": traced_blockers,
            "root_cause_summary": (
                f"Project '{project.name}' has {len(open_blockers)} open blocker(s) "
                f"impacting {sum(len(b.affected_tasks) for b in open_blockers)} task(s)."
            ),
        }

    def coordinate_task_execution(
        self,
        task_id: str,
        target_agent: str = "coding",
    ) -> Dict[str, Any]:
        """
        Coordinates handoff from Project Agent to a specialized agent (coding, research, presentation).
        """
        task = self.prod.tasks.store.get_task(task_id)
        if not task:
            return {"error": f"Task '{task_id}' not found"}

        proj_ctx = {}
        if task.project_id:
            proj_ctx = self.prod.context.get_project_context(task.project_id)

        handoff = self.prod.create_agent_handoff(
            from_agent="project_agent",
            to_agent=target_agent,
            objective=f"Execute task: {task.title}",
            context_data={
                "task_id": task.id,
                "task_title": task.title,
                "task_description": task.description,
                "project_context": proj_ctx,
            },
            artifacts=task.artifacts,
            next_action=f"Perform work for '{task.title}'",
        )

        task.status = TaskStatus.IN_PROGRESS
        self.prod.store.save_task(task)

        return {
            "status": "DISPATCHED",
            "task_id": task.id,
            "target_agent": target_agent,
            "handoff": handoff,
        }
