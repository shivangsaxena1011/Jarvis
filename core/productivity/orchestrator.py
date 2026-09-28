"""
SHIVANI Productivity Orchestrator (Phase 16).
Master coordinator unifying Goals, Projects, Tasks, Priorities, Deadlines,
Dependencies, Daily Planning, Focus Sessions, Reviews, and Cross-Agent Handoffs.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.productivity.context_engine import ContextEngine
from core.productivity.deadline_engine import DeadlineEngine
from core.productivity.dependency_engine import DependencyEngine
from core.productivity.focus_engine import FocusEngine
from core.productivity.goal_manager import GoalManager
from core.productivity.models import (
    Blocker,
    DailyPlan,
    Decision,
    FocusSession,
    Goal,
    Milestone,
    PersonalTask,
    Project,
    TaskPriority,
    TaskStatus,
)
from core.productivity.planning_engine import PlanningEngine
from core.productivity.priority_engine import PriorityEngine
from core.productivity.progress_engine import ProgressEngine
from core.productivity.project_manager import ProjectManager
from core.productivity.review_engine import ReviewEngine
from core.productivity.store import ProductivityStore
from core.productivity.task_manager import TaskManager
from notifications.center import NotificationCenter

logger = logging.getLogger("shivani.productivity.orchestrator")


class ProductivityOrchestrator:
    """Master coordinator for all personal agent and productivity capabilities."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        notification_center: Optional[NotificationCenter] = None,
    ):
        self.store = ProductivityStore(db_path=db_path)
        self.notification_center = notification_center

        self.goals = GoalManager(self.store)
        self.projects = ProjectManager(self.store)
        self.tasks = TaskManager(self.store)
        self.priority = PriorityEngine()
        self.deadlines = DeadlineEngine()
        self.dependencies = DependencyEngine()
        self.planning = PlanningEngine(self.store, self.priority)
        self.context = ContextEngine(self.store)
        self.focus = FocusEngine(self.store, notification_center=notification_center)
        self.reviews = ReviewEngine(self.store)
        self.progress = ProgressEngine()

    # ==========================================================================
    # "WHAT SHOULD I DO?" MODE (Section 41 & 42)
    # ==========================================================================

    def recommend_next_tasks(self, limit: int = 3) -> Dict[str, Any]:
        """
        Provides a transparent shortlist of candidate tasks with explicit reasons.
        Does not dictate life choices—surfaces options grounded in explicit criteria.
        """
        active_project = self.context.get_active_project()
        all_tasks = self.store.list_tasks()
        actionable_tasks = [
            t for t in all_tasks
            if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)
        ]

        if not actionable_tasks:
            return {
                "message": "No pending tasks found. All caught up or ready to plan new goals!",
                "recommendations": [],
            }

        # Check for dependency blockers and update blocked tasks
        for task in actionable_tasks:
            is_blocked, reasons = self.dependencies.get_blocked_status(
                task, {t.id: t for t in all_tasks}
            )
            if is_blocked and task.status != TaskStatus.BLOCKED:
                task.status = TaskStatus.BLOCKED
                task.notes.extend(reasons)
                self.store.save_task(task)

        projects_map = {p.id: p for p in self.store.list_projects()}
        ranked = self.priority.rank_tasks(actionable_tasks, all_tasks, projects_map)

        recommendations = []
        for task, score in ranked[:limit]:
            recommendations.append({
                "task_id": task.id,
                "title": task.title,
                "project_name": projects_map[task.project_id].name if task.project_id in projects_map else "General",
                "priority": task.priority.value,
                "due_date": task.due_date or "No deadline",
                "score": score.total_score,
                "why_surfaced": score.reasons,
            })

        return {
            "message": "Based on deadlines, configured priorities, dependencies, and active project context:",
            "active_project": active_project.name if active_project else "None",
            "recommendations": recommendations,
        }

    # ==========================================================================
    # SMART TASK DECOMPOSITION (Section 31)
    # ==========================================================================

    def propose_task_decomposition(self, complex_goal_or_task: str) -> Dict[str, Any]:
        """
        Decomposes complex requests into a proposed sequence of discrete subtasks.
        Shows proposed subtasks for approval before creating them in the database.
        """
        text = complex_goal_or_task.lower()
        if "android" in text or "companion" in text or "bridge" in text:
            subtasks = [
                "1. Define communication protocol & payloads",
                "2. Implement authentication & pairing handshake",
                "3. Implement device discovery & bridge service",
                "4. Implement command dispatch & execution",
                "5. Implement screenshot capture & UI streaming",
                "6. Implement end-to-end integration tests",
                "7. Documentation & user guide",
            ]
        elif "ocr" in text or "vision" in text or "image" in text:
            subtasks = [
                "1. Gather target documents & images",
                "2. Benchmark OCR engines (Tesseract / Windows OCR)",
                "3. Implement pre-processing pipeline (contrast/deskew)",
                "4. Build structured text extraction adapter",
                "5. Implement visual verification test suite",
                "6. Integrate with Desktop HUD & Chat",
            ]
        elif "api" in text or "backend" in text or "server" in text:
            subtasks = [
                "1. Design OpenAPI schema & data models",
                "2. Implement database models & migrations",
                "3. Build REST endpoints & controllers",
                "4. Implement authentication & rate limiting",
                "5. Unit & integration test coverage",
                "6. Deployment configuration & docs",
            ]
        else:
            subtasks = [
                "1. Research & requirements gathering",
                "2. Design architecture & draft interface",
                "3. Core implementation",
                "4. Test verification & edge case handling",
                "5. Documentation & review",
            ]

        return {
            "request": complex_goal_or_task,
            "proposed_subtasks": subtasks,
            "message": f"Proposed {len(subtasks)} subtasks. Confirm to create these tasks.",
        }

    # ==========================================================================
    # CROSS-AGENT WORKFLOW & STRUCTURED HANDOFF (Section 66 & 79 Test 8)
    # ==========================================================================

    def create_agent_handoff(
        self,
        from_agent: str,
        to_agent: str,
        objective: str,
        context_data: Dict[str, Any],
        artifacts: Optional[List[str]] = None,
        constraints: Optional[List[str]] = None,
        next_action: str = "",
    ) -> Dict[str, Any]:
        """
        Creates a structured, leak-free handoff context between specialized agents
        (e.g., Research -> Coding -> Testing -> Presentation).
        """
        handoff = {
            "handoff_id": f"handoff_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "objective": objective,
            "relevant_context": context_data,
            "artifacts": artifacts or [],
            "constraints": constraints or [],
            "next_action": next_action or f"Execute {to_agent} phase",
        }
        logger.info(f"Agent handoff created from '{from_agent}' to '{to_agent}': {objective}")
        return handoff

    # ==========================================================================
    # PERSONAL DASHBOARD SUMMARY (Section 40)
    # ==========================================================================

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Assembles a live, factual dashboard snapshot from real records.
        """
        all_tasks = self.store.list_tasks()
        all_projects = self.store.list_projects()
        all_goals = self.store.list_goals()
        deadlines = self.deadlines.categorize_deadlines(all_tasks)

        open_tasks = [t for t in all_tasks if t.status in (TaskStatus.TODO, TaskStatus.IN_PROGRESS)]
        critical_tasks = [t for t in open_tasks if t.priority in (TaskPriority.HIGH, TaskPriority.CRITICAL)]

        return {
            "active_tasks_count": len(open_tasks),
            "critical_tasks_count": len(critical_tasks),
            "overdue_count": len(deadlines["overdue"]),
            "due_today_count": len(deadlines["today"]),
            "due_tomorrow_count": len(deadlines["tomorrow"]),
            "active_projects": [
                {
                    "id": p.id,
                    "name": p.name,
                    "status": p.status.value,
                    "health": self.projects.get_project_health(p.id)["is_healthy"],
                }
                for p in all_projects if p.status == "ACTIVE"
            ],
            "active_goals": [
                {
                    "id": g.id,
                    "title": g.title,
                    "progress": g.progress,
                    "category": g.category,
                }
                for g in all_goals if g.status == "ACTIVE"
            ],
            "focus_session_active": self.focus.is_focusing,
            "active_focus_task": self.focus.active_session.task_title if self.focus.active_session else None,
        }
