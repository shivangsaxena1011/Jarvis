"""
SHIVANI Productivity OS Tools (Phase 16).
Registers standard tools for Tasks, Projects, Goals, Planning, and Focus Mode.
"""

from typing import Any, Dict, List, Optional
from core.productivity.models import TaskPriority
from core.productivity.orchestrator import ProductivityOrchestrator
from security.permissions.models import RiskLevel
from tools.base import BaseTool


class TaskCreateTool(BaseTool):
    """Creates a new personal task with due date, priority, and project link."""
    name = "task.create"
    description = "Create a personal task with priority, due date, and project association."
    permission_level = RiskLevel.SAFE

    def __init__(self, productivity: ProductivityOrchestrator):
        super().__init__()
        self.prod = productivity

    async def run(self, **kwargs) -> Dict[str, Any]:
        title = kwargs.get("title")
        if not title:
            return {"success": False, "error": "Missing 'title'"}

        description = kwargs.get("description", "")
        priority_str = str(kwargs.get("priority", "MEDIUM")).upper()
        priority = getattr(TaskPriority, priority_str, TaskPriority.MEDIUM)
        project_id = kwargs.get("project_id")
        due_date = kwargs.get("due_date")
        estimated_duration = int(kwargs.get("estimated_duration_minutes", 30))

        task = self.prod.tasks.create_task(
            title=title,
            description=description,
            priority=priority,
            project_id=project_id,
            due_date=due_date,
            estimated_duration_minutes=estimated_duration,
        )
        return {
            "success": True,
            "task_id": task.id,
            "title": task.title,
            "priority": task.priority.value,
            "status": task.status.value,
            "due_date": task.due_date,
        }


class TaskListTool(BaseTool):
    """Lists personal tasks filtered by status or project."""
    name = "task.list"
    description = "List active or filtered personal tasks."
    permission_level = RiskLevel.SAFE

    def __init__(self, productivity: ProductivityOrchestrator):
        super().__init__()
        self.prod = productivity

    async def run(self, **kwargs) -> Dict[str, Any]:
        project_id = kwargs.get("project_id")
        status = kwargs.get("status")
        tasks = self.prod.store.list_tasks(project_id=project_id, status=status)
        return {
            "success": True,
            "count": len(tasks),
            "tasks": [
                {
                    "id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "priority": t.priority.value,
                    "due_date": t.due_date,
                    "project_id": t.project_id,
                }
                for t in tasks
            ],
        }


class TaskCompleteTool(BaseTool):
    """Completes a task through the strict completion verification gate."""
    name = "task.complete"
    description = "Mark a task as COMPLETED with outcome verification."
    permission_level = RiskLevel.SAFE

    def __init__(self, productivity: ProductivityOrchestrator):
        super().__init__()
        self.prod = productivity

    async def run(self, **kwargs) -> Dict[str, Any]:
        task_id = kwargs.get("task_id")
        if not task_id:
            return {"success": False, "error": "Missing 'task_id'"}

        notes = kwargs.get("notes", "")
        artifact_path = kwargs.get("artifact_path")
        exec_output = {"manually_confirmed": True}
        if artifact_path:
            exec_output["artifact_path"] = artifact_path

        verified, failures = self.prod.tasks.complete_task(task_id, execution_output=exec_output)
        if not verified:
            return {
                "success": False,
                "error": f"Completion gate rejected: {'; '.join(failures)}",
                "failures": failures,
            }

        return {"success": True, "task_id": task_id, "status": "COMPLETED"}


class ProjectContextTool(BaseTool):
    """Retrieves factual context and continuity snapshot for a project."""
    name = "project.context"
    description = "Get structured project context, active milestone, blockers, and open tasks."
    permission_level = RiskLevel.SAFE

    def __init__(self, productivity: ProductivityOrchestrator):
        super().__init__()
        self.prod = productivity

    async def run(self, **kwargs) -> Dict[str, Any]:
        project_name_or_id = kwargs.get("project_id") or kwargs.get("name")
        if not project_name_or_id:
            # Fall back to active project
            active = self.prod.context.get_active_project()
            if active:
                project_name_or_id = active.id
            else:
                return {"success": False, "error": "No project specified and no active project context."}

        summary = self.prod.context.get_continuity_summary(project_name_or_id)
        return {"success": True, "context": summary}


class PlanTodayTool(BaseTool):
    """Generates a proposed daily schedule plan based on active tasks and deadlines."""
    name = "plan.today"
    description = "Generate a proposed daily schedule based on tasks, deadlines, and priorities."
    permission_level = RiskLevel.SAFE

    def __init__(self, productivity: ProductivityOrchestrator):
        super().__init__()
        self.prod = productivity

    async def run(self, **kwargs) -> Dict[str, Any]:
        available_hours = float(kwargs.get("available_hours", 8.0))
        plan, warning = self.prod.planning.generate_daily_plan(
            available_minutes=int(available_hours * 60)
        )
        return {
            "success": True,
            "plan_id": plan.id,
            "date": plan.date,
            "time_blocks": [b.model_dump() for b in plan.time_blocks],
            "total_planned_minutes": plan.total_planned_minutes,
            "warning": warning,
        }
