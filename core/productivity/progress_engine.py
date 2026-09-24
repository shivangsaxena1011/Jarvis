"""
SHIVANI Progress Engine (Phase 16).
Computes objective, verified progress for Goals, Milestones, and Projects.
Strictly grounded in completed deliverables, not subjective heuristics.
"""

from typing import List, Optional
from core.productivity.models import (
    Goal,
    Milestone,
    MilestoneStatus,
    PersonalTask,
    Project,
    TaskStatus,
)


class ProgressEngine:
    """Calculates factual progress percentages based on verified milestones and tasks."""

    @staticmethod
    def calculate_milestone_progress(
        milestone: Milestone,
        tasks: List[PersonalTask],
    ) -> float:
        """
        Progress of a milestone = completed_tasks / total_tasks in milestone.
        If milestone status is COMPLETED, progress is 1.0.
        """
        if milestone.status == MilestoneStatus.COMPLETED:
            return 1.0

        m_tasks = [t for t in tasks if t.milestone_id == milestone.id or t.id in milestone.tasks]
        if not m_tasks:
            return 0.0

        completed = sum(1 for t in m_tasks if t.status == TaskStatus.COMPLETED)
        return round(completed / len(m_tasks), 2)

    @staticmethod
    def calculate_goal_progress(
        goal: Goal,
        milestones: List[Milestone],
        tasks: Optional[List[PersonalTask]] = None,
    ) -> float:
        """
        Progress of a goal = completed_milestones / total_milestones.
        If no milestones exist, falls back to completed_tasks / total_tasks.
        """
        g_milestones = [m for m in milestones if m.goal_id == goal.id or m.id in goal.milestones]
        if g_milestones:
            completed_m = sum(1 for m in g_milestones if m.status == MilestoneStatus.COMPLETED)
            return round(completed_m / len(g_milestones), 2)

        if tasks:
            g_tasks = [t for t in tasks if t.goal_id == goal.id or t.id in goal.tasks]
            if g_tasks:
                completed_t = sum(1 for t in g_tasks if t.status == TaskStatus.COMPLETED)
                return round(completed_t / len(g_tasks), 2)

        return 0.0

    @staticmethod
    def calculate_project_progress(
        project: Project,
        milestones: List[Milestone],
        tasks: List[PersonalTask],
    ) -> float:
        """
        Calculates project progress as a combined metric:
        Milestone completion (70% weight) + Task completion (30% weight).
        If only tasks exist, 100% based on tasks.
        """
        p_milestones = [m for m in milestones if m.project_id == project.id or m.id in project.milestones]
        p_tasks = [t for t in tasks if t.project_id == project.id or t.id in project.tasks]

        if not p_milestones and not p_tasks:
            return 0.0

        if p_milestones and p_tasks:
            m_comp = sum(1 for m in p_milestones if m.status == MilestoneStatus.COMPLETED) / len(p_milestones)
            t_comp = sum(1 for t in p_tasks if t.status == TaskStatus.COMPLETED) / len(p_tasks)
            return round((m_comp * 0.7) + (t_comp * 0.3), 2)
        elif p_milestones:
            m_comp = sum(1 for m in p_milestones if m.status == MilestoneStatus.COMPLETED) / len(p_milestones)
            return round(m_comp, 2)
        else:
            t_comp = sum(1 for t in p_tasks if t.status == TaskStatus.COMPLETED) / len(p_tasks)
            return round(t_comp, 2)
