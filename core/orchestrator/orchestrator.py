"""
SHIVANI Central Orchestrator
Master coordinator integrating context, intent parsing, planning, permissions,
tool execution, emergency stop, and event broadcasting.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from core.config import Settings, get_settings
from core.llm.base import LLMProvider
from core.llm.factory import create_llm_provider
from security.permissions.engine import PermissionEngine
from security.audit.logger import AuditLogger
from tools.registry import ToolRegistry
from core.orchestrator.state_machine import Task, TaskState
from core.orchestrator.emergency import EmergencyStop
from core.context.normalizer import HinglishNormalizer, SessionContext
from core.orchestrator.planner import TaskPlanner
from core.orchestrator.executor import TaskExecutor

# Default baseline tools
from tools.computer.system_tools import ScreenshotTool, GetActiveWindowTool, ListProcessesTool, OpenAppTool
from tools.filesystem.file_tools import ListDirectoryTool, ReadFileTool, WriteFileTool, SafeDeleteTool
from tools.terminal.shell_tools import TerminalExecuteTool


class Orchestrator:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm_provider: Optional[LLMProvider] = None,
        permission_engine: Optional[PermissionEngine] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self.settings = settings or get_settings()
        self.llm = llm_provider or create_llm_provider(self.settings)
        self.permissions = permission_engine or PermissionEngine(policy=self.settings.SECURITY_POLICY)
        self.audit = audit_logger or AuditLogger(log_path=self.settings.AUDIT_LOG_PATH)
        
        self.tools = ToolRegistry(permission_engine=self.permissions, audit_logger=self.audit)
        self.emergency = EmergencyStop()
        self.context = SessionContext()
        
        self.planner = TaskPlanner(self.llm, self.tools)
        self.executor = TaskExecutor(self.tools, self.emergency)

        self._tasks: Dict[str, Task] = {}
        self._event_listeners: List[Callable[[str, Dict[str, Any]], None]] = []

        # Auto-register baseline tools
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        default_tools = [
            ScreenshotTool(),
            GetActiveWindowTool(),
            ListProcessesTool(),
            OpenAppTool(),
            ListDirectoryTool(),
            ReadFileTool(),
            WriteFileTool(),
            SafeDeleteTool(),
            TerminalExecuteTool(),
        ]
        for t in default_tools:
            self.tools.register(t)

    def add_event_listener(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        self._event_listeners.append(callback)

    def broadcast(self, event_type: str, data: Dict[str, Any]) -> None:
        for listener in self._event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                print(f"[EVENT LISTENER ERROR] {e}")

    async def submit_task(self, query: str) -> Task:
        # Reset emergency stop state if previously triggered
        if self.emergency.is_stopped:
            self.emergency.reset()

        task = Task(user_query=query)
        self._tasks[task.id] = task

        # Strip wake word if present
        clean_query = HinglishNormalizer.strip_wake_word(query, wake_word=self.settings.WAKE_WORD)
        # Normalize Hindi/Hinglish instructions
        task.normalized_query = HinglishNormalizer.normalize(clean_query, self.context)

        self.audit.log_event("task_created", task_id=task.id, details={"query": query, "normalized": task.normalized_query})
        self.broadcast("task_created", {"task": task.model_dump()})

        # Run task execution asynchronously
        async_task = asyncio.create_task(self._run_task_pipeline(task))
        self.emergency.register_task(task.id, async_task)

        return task

    async def _run_task_pipeline(self, task: Task) -> None:
        try:
            # 1. PLANNING PHASE
            task.transition_to(TaskState.PLANNING, f"Analyzing intent: '{task.normalized_query}'")
            self.broadcast("task_updated", {"task": task.model_dump()})

            plan = await self.planner.create_plan(
                query=task.user_query,
                normalized_query=task.normalized_query,
                context=self.context
            )
            task.plan = plan
            self.audit.log_event("plan_generated", task_id=task.id, details={"plan": plan.model_dump()})
            self.broadcast("task_updated", {"task": task.model_dump()})

            # 2. EXECUTION & VERIFICATION PHASE
            def on_step(t: Task, step_msg: str):
                self.broadcast("step_progress", {"task_id": t.id, "message": step_msg})

            await self.executor.execute_task(task, on_step_update=on_step)

            # 3. CONTEXT UPDATE
            if task.state == TaskState.COMPLETED:
                self.context.recent_history.append(task.user_query)

        except asyncio.CancelledError:
            task.transition_to(TaskState.CANCELLED, "Task aborted by user or emergency stop.")
            task.error = "Cancelled"
        except Exception as e:
            task.transition_to(TaskState.FAILED, f"Unhandled exception: {e}")
            task.error = str(e)
            self.audit.log_event("task_error", task_id=task.id, error=str(e), success=False)
        finally:
            self.emergency.unregister_task(task.id)
            self.broadcast("task_completed", {"task": task.model_dump()})

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 50) -> List[Task]:
        return list(self._tasks.values())[-limit:]

    def approve_request(self, request_id: str, approved: bool, resolved_by: str = "user") -> bool:
        success = self.permissions.resolve_request(request_id, approved, resolved_by=resolved_by)
        if success:
            req = self.permissions.get_request(request_id)
            self.audit.log_event("approval_resolved", task_id=req.task_id if req else None, details={"request_id": request_id, "approved": approved, "by": resolved_by})
            self.broadcast("approval_resolved", {"request_id": request_id, "approved": approved})
        return success

    def stop_all(self) -> int:
        count = self.emergency.trigger_stop_all()
        # Immediately transition any in-flight tasks to CANCELLED
        for task in self._tasks.values():
            if task.state in (
                TaskState.PENDING,
                TaskState.PLANNING,
                TaskState.WAITING_FOR_PERMISSION,
                TaskState.EXECUTING,
                TaskState.VERIFYING,
                TaskState.RECOVERING,
            ):
                task.transition_to(TaskState.CANCELLED, "Emergency Stop aborted active task.")
                task.error = "Cancelled by Emergency Stop"

        self.audit.log_event("emergency_stop_triggered", details={"tasks_cancelled": count})
        self.broadcast("emergency_stop", {"cancelled_count": count})
        return count

