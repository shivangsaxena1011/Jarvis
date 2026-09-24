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
    VisualInspectTool,
    VisualFindElementTool,
    VisualOCRTool,
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

# Phase 6: Coding, Presentation & Documentation Agents and Tools
from core.artifacts.manager import ArtifactManager
from agents.coding.agent import CodingAgent
from agents.research.agent import ResearchAgent
from agents.presentation.agent import PresentationAgent
from agents.documentation.agent import DocumentationAgent

from tools.coding import (
    CodingInspectProjectTool,
    CodingSearchCodeTool,
    CodingFindSymbolTool,
    CodingReadCodeFileTool,
    CodingApplyPatchTool,
    CodingCreateFileTool,
    CodingRunTestsTool,
    CodingRunBuildTool,
    CodingAnalyzeErrorTool,
    CodingGitStatusTool,
    CodingGitDiffTool,
    CodingGitCommitTool,
    CodingGitPushTool,
)
from tools.presentation import (
    PresentationGenerateDeckTool,
    PresentationGeneratePitchTool,
    PresentationGenerateQATool,
)
from tools.documentation import (
    DocumentationGenerateReadmeTool,
    DocumentationGenerateApiDocsTool,
    DocumentationGenerateArchDocTool,
)

# Phase 7: Android Phone Agent & Device Bridge
from core.bridge.device_bridge import DeviceBridge
from core.bridge.mock_device import MockAndroidDevice
from core.bridge.models import DeviceIdentity
from agents.phone.agent import PhoneAgent
from tools.android import (
    AndroidGetDeviceStatusTool,
    AndroidPairDeviceTool,
    AndroidDisconnectDeviceTool,
    AndroidLaunchAppTool,
    AndroidCloseAppTool,
    AndroidOpenSettingsTool,
    AndroidPressHomeTool,
    AndroidPressBackTool,
    AndroidScreenshotTool,
    AndroidGetVisibleUITool,
    AndroidTapTool,
    AndroidLongPressTool,
    AndroidSwipeTool,
    AndroidTypeTool,
    AndroidListPhotosTool,
    AndroidSelectPhotoTool,
    AndroidTransferFileTool,
    AndroidGetNotificationsTool,
    AndroidReadClipboardTool,
    AndroidWriteClipboardTool,
    AndroidPrepareSocialActionTool,
    AndroidExecuteSocialActionTool,
)

# Phase 8: Memory, Multi-Agent Orchestration, Resource Locking, Notifications, and Scheduler
from memory.manager import MemoryManager
from memory.models import MemoryCategory, MemoryScope, MemorySource
from core.context.builder import ContextBuilder
from core.context.conversational import get_conversational_context
from core.concurrency.resource_manager import ResourceManager
from core.agents import (
    AgentRegistry,
    AgentDescriptor,
    TaskDecomposer,
    TaskDAG,
    SubTask,
    TaskStage,
    AgentMessage,
    AgentResponse,
)
from notifications.center import NotificationCenter, NotificationCategory
from core.scheduler.scheduler import SchedulerService
from tools.memory import (
    MemoryGetPreferenceTool,
    MemorySetPreferenceTool,
    MemorySearchTool,
    MemoryForgetTool,
    MemoryExplainTool,
)
from tools.scheduler import (
    SchedulerListJobsTool,
    SchedulerScheduleJobTool,
    SchedulerCancelJobTool,
)
from tools.notifications import (
    NotificationsListTool,
    NotificationsDismissTool,
)

# Phase 9: Hardening, Recovery, Idempotency, Limits & Operational Modes
from recovery.recovery_engine import RecoveryEngine
from core.idempotency import IdempotencyManager
from core.limits import ExecutionLimits, DEFAULT_LIMITS
from core.modes import SafeModeController, DemoModeController

# Phase 11: Advanced Agentic Planning, TaskGraphs, and Replanning
from planning.planner import AdvancedPlanner, get_advanced_planner
from planning.models import Goal, ExecutionStrategy, SubTaskStatus, ReplanTrigger

# Phase 12: Knowledge OS & Tools
from knowledge.service import KnowledgeOS, get_knowledge_os
from tools.knowledge_tools import (
    KnowledgeSearchTool,
    KnowledgeGetProjectContextTool,
    KnowledgeIndexPathTool,
    KnowledgeQueryGraphTool,
    KnowledgeAddNoteTool,
)

from planning.dependency_graph import TaskGraph

# Phase 13: Extensibility, Universal Skills, App Connectors & Adapters
from skills.registry import SkillRegistry
from skills.lifecycle import SkillLifecycleManager
from connectors.registry import ConnectorRegistry
from connectors.accounts import AccountManager
from adapters.registry import AdapterRegistry
from adapters.browser import BrowserAppAdapter
from adapters.android import AndroidAppAdapter
from tools.skill_tools import (
    SkillListTool,
    SkillInfoTool,
    ConnectorListTool,
    AdapterListTool,
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
        memory_manager: Optional[MemoryManager] = None,
        recovery_engine: Optional[RecoveryEngine] = None,
        idempotency_manager: Optional[IdempotencyManager] = None,
        execution_limits: Optional[ExecutionLimits] = None,
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
        
        # Phase 6: Artifact Manager, Coding, Research, Presentation & Documentation Agents
        self.artifact_manager = ArtifactManager()
        self.coding_agent = CodingAgent()
        self.research_agent = ResearchAgent(research_service=self.research_service, artifact_manager=self.artifact_manager)
        self.presentation_agent = PresentationAgent(artifact_manager=self.artifact_manager)
        self.documentation_agent = DocumentationAgent(artifact_manager=self.artifact_manager)
        
        # Phase 7: Android Phone Agent & Secure Device Bridge
        self.device_bridge = DeviceBridge()
        self.mock_android_device = MockAndroidDevice()
        self.device_bridge.register_transport_handler(self.mock_android_device.handle_command)
        # Pre-register default mock device for seamless local/testing operation
        default_dev = DeviceIdentity(
            device_id="shivani-android-001",
            device_name="Shivani Phone",
            pairing_state="paired",
            connection_status="connected",
            battery_level=88
        )
        self.device_bridge.register_paired_device(default_dev)
        self.phone_agent = PhoneAgent(bridge=self.device_bridge)

        # Phase 8: Memory, Concurrency, Notifications, Scheduler & Agent Registry
        self.memory = memory_manager or MemoryManager(db_path=getattr(self.settings, "MEMORY_DB_PATH", "data/memory.db"))
        self.resources = ResourceManager()
        self.notifications = NotificationCenter(event_bus=self.events)
        self.scheduler = SchedulerService()
        self.context_builder = ContextBuilder(
            memory_manager=self.memory,
            os_adapter=self.os_adapter,
            conv_context=get_conversational_context(),
        )

        self.agent_registry = AgentRegistry()
        self._register_subagents()

        self.workflow_engine = WorkflowEngine(
            tool_registry=self.tools,
            permission_engine=self.permissions,
            event_bus=self.events,
            browser_agent=self.browser_agent,
            os_adapter=self.os_adapter,
            artifact_manager=self.artifact_manager
        )
        
        self.planner = TaskPlanner(self.llm, self.tools)
        self.executor = TaskExecutor(self.tools, self.emergency, event_bus=self.events)

        # Phase 9: Hardening, Recovery, Idempotency, Limits & Operational Modes
        self.recovery = recovery_engine or RecoveryEngine()
        self.idempotency = idempotency_manager or IdempotencyManager()
        self.limits = execution_limits or DEFAULT_LIMITS
        self.safe_mode = SafeModeController()
        self.demo_mode = DemoModeController()

        # Phase 12: Knowledge OS
        self.knowledge_os = get_knowledge_os()

        # Phase 13: Extensibility, Universal Skills, Connectors, Adapters
        self.skill_registry = SkillRegistry(tool_registry=self.tools, agent_registry=self.agent_registry)
        self.skill_lifecycle = SkillLifecycleManager(registry=self.skill_registry)
        self.account_manager = AccountManager()
        self.connector_registry = ConnectorRegistry(account_manager=self.account_manager)
        self.adapter_registry = AdapterRegistry()
        self.adapter_registry.register_adapter(BrowserAppAdapter(browser_agent=self.browser_agent))
        self.adapter_registry.register_adapter(AndroidAppAdapter("android", "com.android.settings", device_bridge=self.device_bridge))


        # Register Emergency Abort Callbacks
        self.emergency.register_abort_callback(
            "browser_shutdown",
            lambda: asyncio.create_task(self.browser_agent.close()) if hasattr(self.browser_agent, "close") else None
        )
        self.emergency.register_abort_callback(
            "device_disconnect",
            lambda: self.device_bridge.disconnect() if hasattr(self.device_bridge, "disconnect") else None
        )

        self._tasks: Dict[str, Task] = {}

        # Auto-register tools across all phases
        self._register_default_tools()


    def _register_subagents(self) -> None:
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="computer_agent",
                description="Controls Windows desktop applications, windows, and input",
                capabilities=["desktop", "window", "input", "clipboard"],
                keywords=["open", "close", "window", "click", "type", "mouse"],
                risk_tier="SAFE",
            ),
            instance=self.computer_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="browser_agent",
                description="Controls web browsers, search, tabs, and web extraction",
                capabilities=["web", "browser", "youtube", "linkedin", "gmail"],
                keywords=["browser", "chrome", "youtube", "website", "search"],
                risk_tier="SAFE",
            ),
            instance=self.browser_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="coding_agent",
                description="Inspects code, fixes bugs, runs tests and git",
                capabilities=["code", "git", "tests", "build"],
                keywords=["code", "git", "bug", "patch", "test", "build"],
                risk_tier="SENSITIVE",
            ),
            instance=self.coding_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="research_agent",
                description="Conducts web and technical research and compiles reports",
                capabilities=["research", "search", "summarize"],
                keywords=["research", "report", "arxiv", "paper"],
                risk_tier="SAFE",
            ),
            instance=self.research_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="presentation_agent",
                description="Generates presentation slides and pitch decks",
                capabilities=["slides", "powerpoint", "presentation"],
                keywords=["presentation", "deck", "slides", "ppt"],
                risk_tier="SAFE",
            ),
            instance=self.presentation_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="documentation_agent",
                description="Generates READMEs and API / architecture documentation",
                capabilities=["documentation", "markdown", "architecture"],
                keywords=["readme", "documentation", "api docs"],
                risk_tier="SAFE",
            ),
            instance=self.documentation_agent,
        )
        self.agent_registry.register_agent(
            AgentDescriptor(
                name="phone_agent",
                description="Controls paired Android phone via secure device bridge",
                capabilities=["android", "phone", "mobile", "notifications"],
                keywords=["phone", "mobile", "android", "insta"],
                risk_tier="SAFE",
            ),
            instance=self.phone_agent,
        )

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
            # Screen capture & vision tools
            ScreenshotTool(screen_capture=scr_cap),
            VisualInspectTool(),
            VisualFindElementTool(),
            VisualOCRTool(),
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
            # Phase 6: Coding tools
            CodingInspectProjectTool(coding_agent=self.coding_agent),
            CodingSearchCodeTool(coding_agent=self.coding_agent),
            CodingFindSymbolTool(coding_agent=self.coding_agent),
            CodingReadCodeFileTool(coding_agent=self.coding_agent),
            CodingApplyPatchTool(coding_agent=self.coding_agent),
            CodingCreateFileTool(coding_agent=self.coding_agent),
            CodingRunTestsTool(coding_agent=self.coding_agent),
            CodingRunBuildTool(coding_agent=self.coding_agent),
            CodingAnalyzeErrorTool(coding_agent=self.coding_agent),
            CodingGitStatusTool(coding_agent=self.coding_agent),
            CodingGitDiffTool(coding_agent=self.coding_agent),
            CodingGitCommitTool(coding_agent=self.coding_agent),
            CodingGitPushTool(coding_agent=self.coding_agent),
            # Phase 6: Presentation tools
            PresentationGenerateDeckTool(presentation_agent=self.presentation_agent),
            PresentationGeneratePitchTool(presentation_agent=self.presentation_agent),
            PresentationGenerateQATool(presentation_agent=self.presentation_agent),
            # Phase 6: Documentation tools
            DocumentationGenerateReadmeTool(doc_agent=self.documentation_agent),
            DocumentationGenerateApiDocsTool(doc_agent=self.documentation_agent),
            DocumentationGenerateArchDocTool(doc_agent=self.documentation_agent),
            # Phase 7: Android Phone tools
            AndroidGetDeviceStatusTool(phone_agent=self.phone_agent),
            AndroidPairDeviceTool(bridge=self.device_bridge),
            AndroidDisconnectDeviceTool(bridge=self.device_bridge),
            AndroidLaunchAppTool(phone_agent=self.phone_agent),
            AndroidCloseAppTool(phone_agent=self.phone_agent),
            AndroidOpenSettingsTool(phone_agent=self.phone_agent),
            AndroidPressHomeTool(phone_agent=self.phone_agent),
            AndroidPressBackTool(phone_agent=self.phone_agent),
            AndroidScreenshotTool(phone_agent=self.phone_agent),
            AndroidGetVisibleUITool(phone_agent=self.phone_agent),
            AndroidTapTool(phone_agent=self.phone_agent),
            AndroidLongPressTool(phone_agent=self.phone_agent),
            AndroidSwipeTool(phone_agent=self.phone_agent),
            AndroidTypeTool(phone_agent=self.phone_agent),
            AndroidListPhotosTool(phone_agent=self.phone_agent),
            AndroidSelectPhotoTool(phone_agent=self.phone_agent),
            AndroidTransferFileTool(phone_agent=self.phone_agent),
            AndroidGetNotificationsTool(phone_agent=self.phone_agent),
            AndroidReadClipboardTool(phone_agent=self.phone_agent),
            AndroidWriteClipboardTool(phone_agent=self.phone_agent),
            AndroidPrepareSocialActionTool(phone_agent=self.phone_agent),
            AndroidExecuteSocialActionTool(phone_agent=self.phone_agent),
            # Phase 8: Memory tools
            MemoryGetPreferenceTool(memory_manager=self.memory),
            MemorySetPreferenceTool(memory_manager=self.memory),
            MemorySearchTool(memory_manager=self.memory),
            MemoryForgetTool(memory_manager=self.memory),
            MemoryExplainTool(memory_manager=self.memory),
            # Phase 8: Scheduler tools
            SchedulerListJobsTool(scheduler=self.scheduler),
            SchedulerScheduleJobTool(scheduler=self.scheduler),
            SchedulerCancelJobTool(scheduler=self.scheduler),
            # Phase 8: Notification tools
            NotificationsListTool(notification_center=self.notifications),
            NotificationsDismissTool(notification_center=self.notifications),
            # Phase 12: Knowledge OS tools
            KnowledgeSearchTool(knowledge_os=self.knowledge_os),
            KnowledgeGetProjectContextTool(knowledge_os=self.knowledge_os),
            KnowledgeIndexPathTool(knowledge_os=self.knowledge_os),
            KnowledgeQueryGraphTool(knowledge_os=self.knowledge_os),
            KnowledgeAddNoteTool(knowledge_os=self.knowledge_os),
            # Phase 13: Extensibility & Universal Skills tools
            SkillListTool(registry=self.skill_registry),
            SkillInfoTool(registry=self.skill_registry),
            ConnectorListTool(registry=self.connector_registry),
            AdapterListTool(registry=self.adapter_registry),
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

        # Phase 8: Preference-aware resolution (e.g. "open browser" -> user's preferred browser)
        pref_browser = self.memory.get_preference("preferred_browser")
        if pref_browser:
            norm_lower = normalized.lower()
            if "open browser" in norm_lower:
                normalized = normalized.replace("open browser", f"open {pref_browser}")
            elif "open my browser" in norm_lower:
                normalized = normalized.replace("open my browser", f"open {pref_browser}")
            elif "browser kholo" in norm_lower:
                normalized = normalized.replace("browser kholo", f"{pref_browser} kholo")

        task.metadata["normalized_query"] = normalized

        # Audit & Event publish
        self.audit.log_event("task_created", task_id=task.id, details={"query": query, "normalized": normalized})
        self.events.publish(EventType.TASK_CREATED, task_id=task.id, data={"task": task.model_dump()})

        # Launch execution pipeline
        async_task = asyncio.create_task(self._run_task_pipeline(task))
        self.emergency.register_task(task.id, async_task)

        return task

    async def submit_multi_agent_goal(self, goal: str) -> TaskDAG:
        """Decomposes a multi-agent goal into a dependency DAG and coordinates subtask executions."""
        dag = TaskDecomposer.decompose(goal)
        self.audit.log_event("multi_agent_dag_created", details={"dag_id": dag.dag_id, "subtasks": [st.model_dump() for st in dag.subtasks]})

        while not dag.is_all_completed() and not dag.is_failed():
            ready = dag.get_ready_subtasks()
            if not ready:
                break
            for st in ready:
                st.status = "running"
                sub_task = await self.submit_task(st.title)
                while sub_task.status in (
                    TaskStatus.PENDING,
                    TaskStatus.PLANNING,
                    TaskStatus.WAITING_FOR_PERMISSION,
                    TaskStatus.EXECUTING,
                    TaskStatus.VERIFYING,
                ):
                    await asyncio.sleep(0.05)

                if sub_task.status == TaskStatus.COMPLETED:
                    dag.mark_completed(st.id, AgentResponse.success(summary=f"Subtask '{st.title}' completed successfully."))
                else:
                    dag.mark_failed(st.id, f"Subtask '{st.title}' failed: {sub_task.error}")
        return dag

    async def submit_autonomous_goal(self, goal_query: str) -> Dict[str, Any]:
        """
        Phase 11 Autonomous Multi-Agent Goal Execution.
        Parses goal, constructs TaskGraph DAG, coordinates parallel batches,
        and dynamically self-corrects via Replanner on failure.
        """
        planner = get_advanced_planner(self.memory)
        goal, graph, strategy, validation = planner.create_plan_for_goal(goal_query)

        if goal.needs_clarification:
            return {
                "status": "needs_clarification",
                "goal": goal.model_dump(),
                "question": goal.clarification_question,
                "options": goal.clarification_options,
            }

        if not validation.is_valid:
            return {
                "status": "invalid_plan",
                "goal": goal.model_dump(),
                "errors": validation.errors,
            }

        self.audit.log_event("autonomous_goal_planned", details={"goal_id": goal.id, "strategy": strategy.value, "node_count": len(graph.nodes)})

        batches = graph.get_parallel_execution_batches()
        intermediate_outputs: Dict[str, Any] = {}

        for batch in batches:
            for node in batch:
                if node.subtask.status in (SubTaskStatus.COMPLETED, SubTaskStatus.SKIPPED):
                    continue

                node.subtask.status = SubTaskStatus.RUNNING
                sub_task = await self.submit_task(node.subtask.title)

                while sub_task.status in (
                    TaskStatus.PENDING,
                    TaskStatus.PLANNING,
                    TaskStatus.WAITING_FOR_PERMISSION,
                    TaskStatus.EXECUTING,
                    TaskStatus.VERIFYING,
                ):
                    await asyncio.sleep(0.05)

                if sub_task.status == TaskStatus.COMPLETED:
                    res_payload = {"summary": sub_task.result or "Completed", "artifacts": sub_task.metadata.get("artifacts", [])}
                    graph.mark_completed(node.subtask.id, res_payload)
                    intermediate_outputs[node.subtask.id] = res_payload
                else:
                    revised_graph, can_continue, trigger = planner.replan_on_failure(
                        graph=graph,
                        node_id=node.subtask.id,
                        error_message=sub_task.error or "Step failed",
                    )
                    self.audit.log_event("replan_triggered", details={"trigger": trigger.model_dump(), "can_continue": can_continue})

                    if not can_continue:
                        graph.mark_failed(node.subtask.id, sub_task.error or "Failed without recovery")
                        return {
                            "status": "failed",
                            "failed_node": node.subtask.id,
                            "error": sub_task.error,
                            "diagnosis": trigger.diagnosis,
                            "graph": planner.serializer.serialize_to_dict(goal, graph),
                        }

        return {
            "status": "completed",
            "goal": goal.model_dump(),
            "strategy": strategy.value,
            "outputs": intermediate_outputs,
            "graph": planner.serializer.serialize_to_dict(goal, graph),
        }

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

            # Phase 8: Save execution checkpoint in task memory
            self.memory.task_memory.save_checkpoint(
                task_id=task.id,
                stage="EXECUTING",
                step_index=0,
                state={"query": task.user_request, "normalized": task.metadata.get("normalized_query")},
            )

            await self.executor.execute_task(task, on_step_update=on_step)

            # 3. CONTEXT & MEMORY UPDATE
            if task.status == TaskStatus.COMPLETED:
                self.context.recent_history.append(task.user_request)
                self.memory.episodic.record_episode(
                    task_id=task.id,
                    query=task.user_request,
                    summary=f"Task completed successfully: {task.metadata.get('normalized_query', task.user_request)}",
                    status="completed",
                    artifacts=task.metadata.get("artifacts", []),
                )
                self.memory.task_memory.clear_checkpoint(task.id)

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
        try:
            if hasattr(self, "phone_agent") and self.phone_agent:
                self.phone_agent.emergency_stop()
        except Exception:
            pass
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

    async def resume_workflow_from_checkpoint(self, workflow_id: str, stage: Optional[str] = None) -> WorkflowResult:
        """Resumes a workflow from its latest checkpoint or a specific stage."""
        return await self.workflow_engine.resume_from_checkpoint(workflow_id, stage=stage)

    async def shutdown(self) -> None:
        """Gracefully stops all active tasks and cleans up browser sessions."""
        self.stop_all()
        try:
            await self.browser_agent.close()
        except Exception:
            pass

