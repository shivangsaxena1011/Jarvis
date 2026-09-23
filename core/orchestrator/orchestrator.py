"""
SHIVANI Central Orchestrator
Master coordinator integrating context, intent parsing, planning, permissions,
tool execution, emergency stop, and event bus emissions.
"""

import asyncio
from typing import Any, Callable, Dict, List, Optional
from core.config import Settings, get_settings
from core.providers.base import LLMProvider
from core.providers.factory import create_provider
from security.permissions.engine import PermissionEngine
from security.audit.logger import AuditLogger
from tools.registry import ToolRegistry
from core.tasks.task import Task, TaskStatus
from core.events.bus import EventBus, EventType, get_event_bus
from core.orchestrator.emergency import EmergencyStop
from core.context.normalizer import HinglishNormalizer, SessionContext
from core.planner.planner import TaskPlanner
from core.executor.executor import TaskExecutor

# System & Computer Tools
from tools.computer.system_tools import (
    ScreenshotTool,
    ActiveWindowTool,
    GetActiveWindowTool,
    ListProcessesTool,
    OpenAppTool,
    CloseAppTool,
    ListWindowsTool,
)

# Filesystem Foundation Tools
from tools.filesystem.file_tools import (
    ListDirectoryTool,
    LegacyListDirTool,
    SearchFilesTool,
    ReadMetadataTool,
    CreateDirectoryTool,
    ReadFileTool,
    WriteFileTool,
)

# Terminal Tool
from tools.terminal.shell_tools import TerminalExecuteTool


class Orchestrator:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm_provider: Optional[LLMProvider] = None,
        permission_engine: Optional[PermissionEngine] = None,
        audit_logger: Optional[AuditLogger] = None,
        event_bus: Optional[EventBus] = None
    ):
        self.settings = settings or get_settings()
        self.events = event_bus or get_event_bus()
        self.llm = llm_provider or create_provider(self.settings)
        self.permissions = permission_engine or PermissionEngine(policy=self.settings.SECURITY_POLICY)
        self.audit = audit_logger or AuditLogger(log_path=self.settings.AUDIT_LOG_PATH)
        
        self.tools = ToolRegistry(permission_engine=self.permissions, audit_logger=self.audit)
        self.emergency = EmergencyStop()
        self.context = SessionContext()
        
        self.planner = TaskPlanner(self.llm, self.tools)
        self.executor = TaskExecutor(self.tools, self.emergency, event_bus=self.events)

        self._tasks: Dict[str, Task] = {}

        # Auto-register Phase 1 foundation tools
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        default_tools = [
            ScreenshotTool(),
            ActiveWindowTool(),
            GetActiveWindowTool(),
            ListWindowsTool(),
            ListProcessesTool(),
            OpenAppTool(),
            CloseAppTool(),
            ListDirectoryTool(),
            LegacyListDirTool(),
            SearchFilesTool(),
            ReadMetadataTool(),
            CreateDirectoryTool(),
            ReadFileTool(),
            WriteFileTool(),
            TerminalExecuteTool(),
        ]
        for t in default_tools:
            self.tools.register(t)

    async def submit_task(self, query: str) -> Task:
        if self.emergency.is_stopped:
            self.emergency.reset()

        task = Task(user_request=query)
        self._tasks[task.id] = task

        # Clean wake word and normalize Hinglish/Hindi
        clean_query = HinglishNormalizer.strip_wake_word(query, wake_word=self.settings.WAKE_WORD)
        normalized = HinglishNormalizer.normalize(clean_query, self.context)
        task.metadata["normalized_query"] = normalized

        # Audit & Event publish
        self.audit.log_event("task_created", task_id=task.id, details={"query": query, "normalized": normalized})
        self.events.publish(EventType.TASK_CREATED, task_id=task.id, data={"task": task.model_dump()})

        # Launch execution pipeline
        async_task = asyncio.create_task(self._run_task_pipeline(task))
        self.emergency.register_task(task.id, async_task)

        return task

    async def _run_task_pipeline(self, task: Task) -> None:
        try:
            # 1. PLANNING PHASE
            task.transition_to(TaskStatus.PLANNING, f"Analyzing intent: '{task.metadata.get('normalized_query')}'")
            self.events.publish(EventType.TASK_PLANNED, task_id=task.id, data={"task": task.model_dump()})

            plan = await self.planner.create_plan(
                query=task.user_request,
                normalized_query=task.metadata.get("normalized_query", task.user_request),
                context=self.context
            )
            task.plan = plan
            self.audit.log_event("plan_generated", task_id=task.id, details={"plan": plan.model_dump()})

            # Check if any step requires confirmation
            if any(s.requires_confirmation for s in plan.steps):
                task.requires_confirmation = True
                self.events.publish(EventType.TASK_WAITING_APPROVAL, task_id=task.id, data={"plan": plan.model_dump()})

            # 2. EXECUTION & VERIFICATION PHASE
            def on_step(t: Task, step_msg: str):
                self.events.publish(EventType.TASK_STARTED, task_id=t.id, data={"message": step_msg})

            await self.executor.execute_task(task, on_step_update=on_step)

            # 3. CONTEXT UPDATE
            if task.status == TaskStatus.COMPLETED:
                self.context.recent_history.append(task.user_request)

        except asyncio.CancelledError:
            task.transition_to(TaskStatus.CANCELLED, "Task aborted by user or emergency stop.")
            task.error = "Cancelled"
            self.events.publish(EventType.TASK_CANCELLED, task_id=task.id, data={"task": task.model_dump()})
        except Exception as e:
            task.transition_to(TaskStatus.FAILED, f"Unhandled exception: {e}")
            task.error = str(e)
            self.audit.log_event("task_error", task_id=task.id, error=str(e), success=False)
            self.events.publish(EventType.TASK_FAILED, task_id=task.id, data={"error": str(e)})
        finally:
            self.emergency.unregister_task(task.id)

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks(self, limit: int = 50) -> List[Task]:
        return list(self._tasks.values())[-limit:]

    def cancel_task(self, task_id: str) -> bool:
        cancelled = self.emergency.trigger_stop_task(task_id)
        task = self._tasks.get(task_id)
        if task and task.status in (
            TaskStatus.PENDING,
            TaskStatus.PLANNING,
            TaskStatus.WAITING_FOR_PERMISSION,
            TaskStatus.EXECUTING,
            TaskStatus.VERIFYING,
            TaskStatus.RECOVERING,
        ):
            task.transition_to(TaskStatus.CANCELLED, "Task cancelled via API cancel endpoint.")
            task.error = "Cancelled by user"
            self.events.publish(EventType.TASK_CANCELLED, task_id=task_id, data={"task": task.model_dump()})
            return True
        return cancelled

    def approve_request(self, request_id: str, approved: bool, resolved_by: str = "user") -> bool:
        success = self.permissions.resolve_request(request_id, approved, resolved_by=resolved_by)
        if success:
            req = self.permissions.get_request(request_id)
            self.audit.log_event("approval_resolved", task_id=req.task_id if req else None, details={"request_id": request_id, "approved": approved, "by": resolved_by})
            self.events.publish(EventType.TASK_WAITING_APPROVAL, data={"request_id": request_id, "approved": approved, "resolved": True})
        return success

    def stop_all(self) -> int:
        count = self.emergency.trigger_stop_all()
        for task in self._tasks.values():
            if task.status in (
                TaskStatus.PENDING,
                TaskStatus.PLANNING,
                TaskStatus.WAITING_FOR_PERMISSION,
                TaskStatus.EXECUTING,
                TaskStatus.VERIFYING,
                TaskStatus.RECOVERING,
            ):
                task.transition_to(TaskStatus.CANCELLED, "Emergency Stop aborted active task.")
                task.error = "Cancelled by Emergency Stop"

        self.audit.log_event("emergency_stop_triggered", details={"tasks_cancelled": count})
        self.events.publish(EventType.TASK_CANCELLED, data={"cancelled_count": count, "emergency": True})
        return count

    async def health_check(self) -> Dict[str, Any]:
        """Runs health checks across runtime, llm provider, tool registry, and events."""
        llm_health = await self.llm.health_check()
        tools_count = len(self.tools.list_tools())
        
        overall_healthy = llm_health.get("healthy", False) and tools_count > 0

        return {
            "status": "healthy" if overall_healthy else "degraded",
            "components": {
                "runtime": "healthy",
                "llm": "healthy" if llm_health.get("healthy") else f"unhealthy ({llm_health.get('error', 'unknown')})",
                "tools": "healthy" if tools_count > 0 else "empty",
                "event_bus": "healthy"
            },
            "details": {
                "registered_tools": tools_count,
                "llm_provider": self.settings.LLM_PROVIDER,
                "llm_health": llm_health,
                "emergency_stopped": self.emergency.is_stopped
            }
        }
