"""
SHIVANI Goal Manager (Phase 16).
Manages strategic personal goals, proposed milestone decompositions,
and objective progress rollups.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from core.productivity.models import (
    Goal,
    GoalStatus,
    Milestone,
    MilestoneStatus,
    TaskPriority,
)
from core.productivity.progress_engine import ProgressEngine
from core.productivity.store import ProductivityStore

logger = logging.getLogger("shivani.productivity.goal_manager")


class GoalManager:
    """Manages strategic user goals and milestone breakdown proposals."""

    def __init__(self, store: ProductivityStore):
        self.store = store

    def create_goal(
        self,
        title: str,
        description: str = "",
        category: str = "General",
        priority: TaskPriority = TaskPriority.MEDIUM,
        target_date: Optional[str] = None,
    ) -> Goal:
        goal = Goal(
            title=title,
            description=description,
            category=category,
            priority=priority,
            target_date=target_date,
        )
        self.store.save_goal(goal)
        logger.info(f"Created goal '{goal.title}' (ID: {goal.id})")
        return goal

    def get_goal(self, goal_id: str) -> Optional[Goal]:
        return self.store.get_goal(goal_id)

    def list_goals(self, status: Optional[str] = None) -> List[Goal]:
        return self.store.list_goals(status=status)

    def update_goal_progress(self, goal_id: str) -> Optional[Goal]:
        """Re-evaluates factual progress for a goal based on milestones."""
        goal = self.store.get_goal(goal_id)
        if not goal:
            return None

        milestones = self.store.list_milestones(goal_id=goal_id)
        tasks = self.store.list_tasks(goal_id=goal_id)
        progress = ProgressEngine.calculate_goal_progress(goal, milestones, tasks)
        goal.progress = progress

        if progress >= 1.0 and goal.status == GoalStatus.ACTIVE:
            goal.status = GoalStatus.COMPLETED

        self.store.save_goal(goal)
        return goal

    def propose_goal_breakdown(
        self,
        goal_title: str,
        category: str = "Project",
    ) -> Dict[str, Any]:
        """
        Supports: 'Help me plan this goal'
        Proposes a structured 5-6 milestone breakdown for user review without silently creating tasks.
        """
        # Sensible, domain-aware standard milestone templates
        if "research" in goal_title.lower() or "study" in goal_title.lower():
            milestone_titles = [
                "Literature Review & Source Gathering",
                "Hypothesis & Methodology Formulation",
                "Data Collection & Synthesis",
                "Drafting Research Findings",
                "Peer Review & Final Report",
            ]
        elif "app" in goal_title.lower() or "build" in goal_title.lower() or "ai" in goal_title.lower():
            milestone_titles = [
                "Requirements & Architecture Design",
                "Proof of Concept / Prototype",
                "Core Implementation",
                "Integration & Comprehensive Testing",
                "Documentation & User Interface",
                "Deployment & Release",
            ]
        else:
            milestone_titles = [
                "Scoping & Definition",
                "Preparation & Resource Setup",
                "Active Execution Phase 1",
                "Active Execution Phase 2",
                "Verification & Finalization",
            ]

        proposed_milestones = []
        for i, title in enumerate(milestone_titles, 1):
            proposed_milestones.append({
                "index": i,
                "title": title,
                "status": "NOT_STARTED",
            })

        return {
            "goal_title": goal_title,
            "category": category,
            "proposed_milestones": proposed_milestones,
            "message": (
                f"Proposed {len(proposed_milestones)} milestones for goal '{goal_title}'. "
                "Review the plan below and approve to instantiate."
            ),
        }

    def instantiate_proposed_milestones(
        self,
        goal_id: str,
        milestone_titles: List[str],
        project_id: Optional[str] = None,
    ) -> List[Milestone]:
        """Instantiates approved milestones into persistent storage."""
        goal = self.store.get_goal(goal_id)
        if not goal:
            raise ValueError(f"Goal '{goal_id}' not found")

        created = []
        prev_id = None
        for title in milestone_titles:
            m = Milestone(
                goal_id=goal_id,
                project_id=project_id,
                title=title,
                status=MilestoneStatus.NOT_STARTED,
                dependencies=[prev_id] if prev_id else [],
            )
            self.store.save_milestone(m)
            goal.milestones.append(m.id)
            created.append(m)
            prev_id = m.id

        self.store.save_goal(goal)
        return created
