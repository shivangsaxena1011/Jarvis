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
from tools.desktop.os import OperatingSystemAdapter, get_os_adapter
from tools.desktop import (
    ApplicationManager,
    WindowManager,
    InputController,
    ScreenCapture,
    ClipboardManager,
    OpenAppTool,
    CloseAppTool,
    FocusAppTool,
    ListAppsTool,
    ActiveWindowTool,
    WindowListTool,
    WindowFocusTool,
    WindowMinimizeTool,
    WindowMaximizeTool,
    WindowRestoreTool,
    WindowCloseTool,
    MouseMoveTool,
    ClickTool,
    DoubleClickTool,
    RightClickTool,
    MouseDragTool,
    MouseScrollTool,
    GetCursorPosTool,
    TypeTool,
    PressKeyTool,
    HotkeyTool,
    ClipboardReadTool,
    ClipboardWriteTool,
    ClipboardClearTool,
    ScreenshotTool,
    OpenFolderTool,
    FindFilesTool,
)
from agents.computer import ComputerAgent, CurrentUIContext

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

# Browser Agent & Tools (Phase 4)
from agents.browser.agent import BrowserAgent
from tools.browser import (
    BrowserOpenTool,
    BrowserCloseTool,
    BrowserNavigateTool,
    BrowserBackTool,
    BrowserForwardTool,
    BrowserRefreshTool,
    BrowserGetTitleTool,
    BrowserGetUrlTool,
    BrowserSearchTool,
    BrowserFindTool,
    BrowserClickTool,
    BrowserDoubleClickTool,
    BrowserTypeTool,
    BrowserClearTool,
    BrowserSelectTool,
    BrowserPressKeyTool,
    BrowserScrollTool,
    BrowserScrollToTool,
    BrowserNewTabTool,
    BrowserSwitchTabTool,
    BrowserCloseTabTool,
    BrowserListTabsTool,
    BrowserExtractTextTool,
    BrowserExtractLinksTool,
    BrowserSummarizeTool,
    BrowserExtractDataTool,
    BrowserScreenshotTool,
    BrowserUploadFileTool,
    BrowserDownloadFileTool,
    BrowserPlayYouTubeTool,
)

# Project, Content & Workflow Engine (Phase 5)
from core.projects.indexer import ProjectIndexer
from agents.content.agent import ContentAgent
from core.workflows.models import Workflow, WorkflowResult, WorkflowStatus
from core.workflows.engine import WorkflowEngine
from integrations.youtube import YouTubeService
from integrations.gmail import GmailService
from integrations.linkedin import LinkedInService
from integrations.github import GitHubService
from integrations.research import ResearchService

from tools.integrations import (
    YouTubeSearchTool,
    YouTubeOpenVideoTool,
    YouTubePlayTool,
    YouTubePauseTool,
    YouTubeStopTool,
    YouTubeGetCurrentVideoTool,
    GmailOpenTool,
    GmailListUnreadTool,
    GmailSearchTool,
    GmailSummarizeTool,
    GmailCleanupProposalTool,
    GmailExecuteCleanupTool,
    GmailDeleteTool,
    LinkedInOpenTool,
    LinkedInReadFeedTool,
    LinkedInPreparePostTool,
    LinkedInPrepareCommentTool,
    LinkedInPublishPostTool,
    GitHubInspectRepositoryTool,
    GitHubReadFileTool,
    GitHubListFilesTool,
    GitHubReadIssuesTool,
    GitHubCreateIssueTool,
    GitHubInspectRunnableTool,
    ResearchSearchTool,
    ResearchOpenSourceTool,
    ResearchSummarizeTool,
    ResearchSaveReportTool,
    ProjectFindTool,
    ProjectListTool,
    ContentGenerateLinkedInPostTool,
    ContentGenerateEmailTool,
    ContentGenerateCommentTool,
    ContentGenerateReadmeTool,
    ContentGeneratePresentationTool,
)


class Orchestrator:
    def __init__(
        self,
        settings: Optional[Settings] = None,
        llm_provider: Optional[LLMProvider] = None,
        permission_engine: Optional[PermissionEngine] = None,
        audit_logger: Optional[AuditLogger] = None,
        event_bus: Optional[EventBus] = None,
        os_adapter: Optional[OperatingSystemAdapter] = None,
        browser_agent: Optional[BrowserAgent] = None,
    ):
        self.settings = settings or get_settings()
        self.os_adapter = os_adapter or get_os_adapter()
        self.events = event_bus or get_event_bus()
        self.llm = llm_provider or create_provider(self.settings)
        self.permissions = permission_engine or PermissionEngine(policy=self.settings.SECURITY_POLICY)
        self.audit = audit_logger or AuditLogger(log_path=self.settings.AUDIT_LOG_PATH)
        
        self.tools = ToolRegistry(permission_engine=self.permissions, audit_logger=self.audit)
        self.emergency = EmergencyStop()
        self.context = SessionContext()
        self.ui_context = CurrentUIContext()
        self.computer_agent = ComputerAgent(adapter=self.os_adapter, context=self.ui_context)
        self.browser_agent = browser_agent or BrowserAgent()

        # Phase 5: Productivity services, indexer, content agent & workflow engine
        self.project_indexer = ProjectIndexer()
        self.content_agent = ContentAgent()
        self.youtube_service = YouTubeService(browser_agent=self.browser_agent)
        self.gmail_service = GmailService(browser_agent=self.browser_agent)
        self.linkedin_service = LinkedInService(browser_agent=self.browser_agent)
        self.github_service = GitHubService(token=self.settings.GITHUB_TOKEN)
        self.research_service = ResearchService(browser_agent=self.browser_agent, output_dir=self.settings.RESEARCH_OUTPUT_DIR)
        self.workflow_engine = WorkflowEngine(tool_registry=self.tools, permission_engine=self.permissions, event_bus=self.events)
        
        self.planner = TaskPlanner(self.llm, self.tools)
        self.executor = TaskExecutor(self.tools, self.emergency, event_bus=self.events)

        self._tasks: Dict[str, Task] = {}

        # Auto-register Phase 1, Phase 3, Phase 4, and Phase 5 tools
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        app_mgr = ApplicationManager(self.os_adapter)
        win_mgr = WindowManager(self.os_adapter)
        inp_ctrl = InputController(self.os_adapter)
        scr_cap = ScreenCapture(self.os_adapter)
        clip_mgr = ClipboardManager(self.os_adapter)

        default_tools = [
            # Desktop application & window tools
            OpenAppTool(app_manager=app_mgr),
            CloseAppTool(app_manager=app_mgr),
            FocusAppTool(window_manager=win_mgr),
            ListAppsTool(app_manager=app_mgr),
            ActiveWindowTool(window_manager=win_mgr),
            WindowListTool(window_manager=win_mgr),
            WindowFocusTool(window_manager=win_mgr),
            WindowMinimizeTool(window_manager=win_mgr),
            WindowMaximizeTool(window_manager=win_mgr),
            WindowRestoreTool(window_manager=win_mgr),
            WindowCloseTool(window_manager=win_mgr),
            # Input tools
            MouseMoveTool(input_controller=inp_ctrl),
            ClickTool(input_controller=inp_ctrl),
            DoubleClickTool(input_controller=inp_ctrl),
            RightClickTool(input_controller=inp_ctrl),
            MouseDragTool(input_controller=inp_ctrl),
            MouseScrollTool(input_controller=inp_ctrl),
            GetCursorPosTool(input_controller=inp_ctrl),
            TypeTool(input_controller=inp_ctrl),
            PressKeyTool(input_controller=inp_ctrl),
            HotkeyTool(input_controller=inp_ctrl),
            # Clipboard tools
            ClipboardReadTool(clipboard_manager=clip_mgr),
            ClipboardWriteTool(clipboard_manager=clip_mgr),
            ClipboardClearTool(clipboard_manager=clip_mgr),
            # Screen capture & file explorer tools
            ScreenshotTool(screen_capture=scr_cap),
            OpenFolderTool(),
            FindFilesTool(),
            # Filesystem tools
            ListDirectoryTool(),
            LegacyListDirTool(),
            SearchFilesTool(),
            ReadMetadataTool(),
            CreateDirectoryTool(),
            ReadFileTool(),
            WriteFileTool(),
            # Terminal tool
            TerminalExecuteTool(),
            # Browser navigation tools
            BrowserOpenTool(browser_agent=self.browser_agent),
            BrowserCloseTool(browser_agent=self.browser_agent),
            BrowserNavigateTool(browser_agent=self.browser_agent),
            BrowserBackTool(browser_agent=self.browser_agent),
            BrowserForwardTool(browser_agent=self.browser_agent),
            BrowserRefreshTool(browser_agent=self.browser_agent),
            BrowserGetTitleTool(browser_agent=self.browser_agent),
            BrowserGetUrlTool(browser_agent=self.browser_agent),
            BrowserSearchTool(browser_agent=self.browser_agent),
            # Browser interaction tools
            BrowserFindTool(browser_agent=self.browser_agent),
            BrowserClickTool(browser_agent=self.browser_agent),
            BrowserDoubleClickTool(browser_agent=self.browser_agent),
            BrowserTypeTool(browser_agent=self.browser_agent),
            BrowserClearTool(browser_agent=self.browser_agent),
            BrowserSelectTool(browser_agent=self.browser_agent),
            BrowserPressKeyTool(browser_agent=self.browser_agent),
            BrowserScrollTool(browser_agent=self.browser_agent),
            BrowserScrollToTool(browser_agent=self.browser_agent),
            # Browser tab tools
            BrowserNewTabTool(browser_agent=self.browser_agent),
            BrowserSwitchTabTool(browser_agent=self.browser_agent),
            BrowserCloseTabTool(browser_agent=self.browser_agent),
            BrowserListTabsTool(browser_agent=self.browser_agent),
            # Browser content & workflow tools
            BrowserExtractTextTool(browser_agent=self.browser_agent),
            BrowserExtractLinksTool(browser_agent=self.browser_agent),
            BrowserSummarizeTool(browser_agent=self.browser_agent),
            BrowserExtractDataTool(browser_agent=self.browser_agent),
            BrowserScreenshotTool(browser_agent=self.browser_agent),
            BrowserUploadFileTool(browser_agent=self.browser_agent),
            BrowserDownloadFileTool(browser_agent=self.browser_agent),
            BrowserPlayYouTubeTool(browser_agent=self.browser_agent),
            # Phase 5: Project & Content tools
            ProjectFindTool(indexer=self.project_indexer),
            ProjectListTool(indexer=self.project_indexer),
            ContentGenerateLinkedInPostTool(agent=self.content_agent),
            ContentGenerateEmailTool(agent=self.content_agent),
            ContentGenerateCommentTool(agent=self.content_agent),
            ContentGenerateReadmeTool(agent=self.content_agent),
            ContentGeneratePresentationTool(agent=self.content_agent),
            # Phase 5: YouTube tools
            YouTubeSearchTool(youtube_service=self.youtube_service),
            YouTubeOpenVideoTool(youtube_service=self.youtube_service),
            YouTubePlayTool(youtube_service=self.youtube_service),
            YouTubePauseTool(youtube_service=self.youtube_service),
            YouTubeStopTool(youtube_service=self.youtube_service),
            YouTubeGetCurrentVideoTool(youtube_service=self.youtube_service),
            # Phase 5: Gmail tools
            GmailOpenTool(gmail_service=self.gmail_service),
            GmailListUnreadTool(gmail_service=self.gmail_service),
            GmailSearchTool(gmail_service=self.gmail_service),
            GmailSummarizeTool(gmail_service=self.gmail_service),
            GmailCleanupProposalTool(gmail_service=self.gmail_service),
            GmailExecuteCleanupTool(gmail_service=self.gmail_service),
            GmailDeleteTool(gmail_service=self.gmail_service),
            # Phase 5: LinkedIn tools
            LinkedInOpenTool(linkedin_service=self.linkedin_service),
            LinkedInReadFeedTool(linkedin_service=self.linkedin_service),
            LinkedInPreparePostTool(linkedin_service=self.linkedin_service),
            LinkedInPrepareCommentTool(linkedin_service=self.linkedin_service),
            LinkedInPublishPostTool(linkedin_service=self.linkedin_service),
            # Phase 5: GitHub tools
            GitHubInspectRepositoryTool(github_service=self.github_service),
            GitHubReadFileTool(github_service=self.github_service),
            GitHubListFilesTool(github_service=self.github_service),
            GitHubReadIssuesTool(github_service=self.github_service),
            GitHubCreateIssueTool(github_service=self.github_service),
            GitHubInspectRunnableTool(github_service=self.github_service),
            # Phase 5: Research tools
            ResearchSearchTool(research_service=self.research_service),
            ResearchOpenSourceTool(research_service=self.research_service),
            ResearchSummarizeTool(research_service=self.research_service),
            ResearchSaveReportTool(research_service=self.research_service),
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

    async def submit_workflow(self, workflow: Workflow) -> WorkflowResult:
        """Executes a multi-step cross-application workflow."""
        return await self.workflow_engine.execute_workflow(workflow)

    async def resume_workflow(self, workflow_id: str, approved: bool = True) -> WorkflowResult:
        """Resumes a paused workflow awaiting human approval."""
        return await self.workflow_engine.resume_workflow(workflow_id, approved=approved)

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Retrieves a tracked workflow by id."""
        return self.workflow_engine.get_workflow(workflow_id)

    async def shutdown(self) -> None:
        """Gracefully stops all active tasks and cleans up browser sessions."""
        self.stop_all()
        try:
            await self.browser_agent.close()
        except Exception:
            pass

