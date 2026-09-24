"""
SHIVANI Mock LLM Provider
Deterministic model provider for zero-cost testing, local execution, and verification.
"""

import time
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan, PlanStep


class MockProvider(LLMProvider):
    name = "mock"

    def __init__(self, canned_plans: Optional[Dict[str, TaskPlan]] = None):
        self.canned_plans = canned_plans or {}

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2
    ) -> str:
        prompt_lower = prompt.lower()
        if "hello" in prompt_lower or "hi" in prompt_lower:
            return "Hello! I am SHIVANI, ready to assist."
        if "who are you" in prompt_lower:
            return "I am SHIVANI, your personal autonomous AI computer agent."
        return "Command understood. Ready to execute."

    async def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        system_prompt: Optional[str] = None
    ) -> BaseModel:
        # Default mock instantiation
        try:
            return schema()
        except Exception:
            return schema.model_validate({})

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        query = user_query.lower().strip()

        for key, plan in self.canned_plans.items():
            if key in query:
                return plan

        # Phase 5: LinkedIn Post Drafting for Project
        if "linkedin" in query and ("post" in query or "draft" in query or "project" in query or "share" in query):
            return TaskPlan(
                goal=user_query,
                rationale="Find local project, generate showcase post, and prepare draft on LinkedIn",
                steps=[
                    PlanStep(
                        id="1",
                        tool="project.find",
                        action="Find target project metadata",
                        arguments={"query": "Heart Disease"},
                        expected_outcome="Project details discovered"
                    ),
                    PlanStep(
                        id="2",
                        tool="content.generate_linkedin_post",
                        action="Draft LinkedIn post for project",
                        arguments={"project_name": "Heart Disease Prediction System"},
                        expected_outcome="LinkedIn post drafted"
                    ),
                    PlanStep(
                        id="3",
                        tool="linkedin.prepare_post",
                        action="Prepare draft post in LinkedIn composer",
                        arguments={"content": "Draft showcase post"},
                        expected_outcome="Draft created on LinkedIn with DRAFT status"
                    )
                ]
            )

        # Phase 5: Gmail Cleanup
        if "gmail" in query and ("clean" in query or "saaf" in query or "cleanup" in query or "archive" in query):
            return TaskPlan(
                goal=user_query,
                rationale="Analyze Gmail inbox and propose cleanup actions requiring user approval",
                steps=[
                    PlanStep(
                        id="1",
                        tool="gmail.propose_cleanup",
                        action="Scan inbox for low-priority and promotional emails",
                        arguments={"max_age_days": 30},
                        expected_outcome="Cleanup proposal generated"
                    )
                ]
            )

        # Phase 5: Gmail Summarization
        if "gmail" in query and ("summarize" in query or "summary" in query or "inbox" in query or "mail" in query):
            return TaskPlan(
                goal=user_query,
                rationale="Read unread Gmail messages and generate executive summary",
                steps=[
                    PlanStep(
                        id="1",
                        tool="gmail.read_inbox",
                        action="Fetch recent inbox messages",
                        arguments={"limit": 10},
                        expected_outcome="Inbox messages retrieved"
                    ),
                    PlanStep(
                        id="2",
                        tool="gmail.summarize",
                        action="Generate executive summary of inbox",
                        arguments={},
                        expected_outcome="Structured email summary generated"
                    )
                ]
            )

        # Phase 6: Presentation Deck Generation
        if ("presentation" in query or "slide" in query or "pitch deck" in query) and not query.startswith("research"):
            return TaskPlan(
                goal=user_query,
                rationale="Generate presentation slides and pitch deck",
                steps=[
                    PlanStep(
                        id="1",
                        tool="presentation.generate_deck",
                        action="Generate presentation slides deck",
                        arguments={
                            "title": "Autonomous AI Agent Architecture",
                            "project_name": "SHIVANI AI",
                            "problem_statement": "Coordinating complex multi-agent goals across applications requires intelligent planning and execution.",
                            "solution_summary": "Unified autonomous agent with vision, tools, and dynamic self-correction.",
                            "tech_stack": ["Python", "Playwright", "FastAPI"],
                            "key_features": ["Dynamic DAGs", "Multi-Agent Orchestration", "Visual Intelligence"],
                        },
                        expected_outcome="Presentation deck generated",
                    )
                ]
            )

        # Phase 6: Documentation Generation
        if "documentation" in query or "readme" in query or "write docs" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Generate documentation and README",
                steps=[
                    PlanStep(
                        id="1",
                        tool="documentation.generate_readme",
                        action="Generate README documentation",
                        arguments={"project_path": "."},
                        expected_outcome="README generated",
                    )
                ]
            )

        # Phase 5: Autonomous Research Workflow
        if "research" in query:
            topic = query.replace("research", "").replace("find", "").replace("papers", "").replace("pe", "").replace("karo", "").strip()
            topic = topic or "Autonomous AI Agents"
            return TaskPlan(
                goal=user_query,
                rationale="Execute multi-source research, synthesize findings with citations, and save report",
                steps=[
                    PlanStep(
                        id="1",
                        tool="research.search",
                        action=f"Search authoritative sources for '{topic}'",
                        arguments={"query": topic, "max_results": 5},
                        expected_outcome="Authoritative sources gathered"
                    ),
                    PlanStep(
                        id="2",
                        tool="research.summarize",
                        action=f"Synthesize structured report with citations for '{topic}'",
                        arguments={"topic": topic},
                        expected_outcome="Structured research report generated"
                    ),
                    PlanStep(
                        id="3",
                        tool="research.save",
                        action="Save research report artifacts to disk",
                        arguments={"query": topic},
                        expected_outcome="Report markdown and sources saved"
                    )
                ]
            )

        # Phase 5: GitHub Repo Inspection & Run Analysis
        if "github" in query:
            repo = "user/repo"
            for token in query.split():
                if "/" in token:
                    repo = token
            return TaskPlan(
                goal=user_query,
                rationale="Inspect GitHub repository and analyze safe runnable entry points",
                steps=[
                    PlanStep(
                        id="1",
                        tool="github.inspect_repo",
                        action=f"Inspect repository structure for '{repo}'",
                        arguments={"repo": repo},
                        expected_outcome="Repository inspected"
                    ),
                    PlanStep(
                        id="2",
                        tool="github.inspect_runnable",
                        action=f"Analyze safe run command and dependencies for '{repo}'",
                        arguments={"repo": repo},
                        expected_outcome="Safe run command analyzed"
                    )
                ]
            )

        # Browser YouTube Playback Task
        if "play" in query or "song" in query or "gana" in query or "arijit" in query:
            song_query = user_query
            for prefix in ["play song", "play", "shivani", "ye song", "is song ko"]:
                if prefix in song_query.lower():
                    song_query = song_query.lower().replace(prefix, "").strip()
            song_query = song_query or "Arijit Singh"
            return TaskPlan(
                goal=user_query,
                rationale="Search and play requested song/video on YouTube",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.play_youtube",
                        action=f"Search YouTube and play '{song_query}'",
                        arguments={"query": song_query},
                        expected_outcome="Song playing on YouTube"
                    )
                ]
            )

        # Browser YouTube Open
        if "youtube" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Open YouTube in web browser",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.open",
                        action="Navigate to YouTube",
                        arguments={"url": "https://www.youtube.com"},
                        expected_outcome="YouTube opened in browser"
                    )
                ]
            )

        # Browser Web Search Task
        if "google" in query or "search" in query or "dhoondo" in query:
            search_query = query.replace("google", "").replace("search", "").replace("pe", "").replace("on", "").strip()
            search_query = search_query or "AI research"
            return TaskPlan(
                goal=user_query,
                rationale="Search the web using search engine",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.search",
                        action=f"Search Google for '{search_query}'",
                        arguments={"query": search_query, "engine": "google"},
                        expected_outcome="Search results displayed"
                    )
                ]
            )

        # Browser Summarize Webpage Task
        if "summarize" in query or "summary" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Summarize active webpage content",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.summarize",
                        action="Extract and summarize current webpage",
                        arguments={},
                        expected_outcome="Structured summary generated"
                    )
                ]
            )

        # Browser Extract Data Task
        if "extract" in query or "information" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Extract important information from active webpage",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.extract_data",
                        action="Extract key information from webpage",
                        arguments={"extraction_type": "general"},
                        expected_outcome="Extracted data structure returned"
                    )
                ]
            )

        # Browser LinkedIn Task
        if "linkedin" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Navigate to LinkedIn",
                steps=[
                    PlanStep(
                        id="1",
                        tool="browser.open",
                        action="Open LinkedIn feed",
                        arguments={"url": "https://www.linkedin.com"},
                        expected_outcome="LinkedIn opened in browser"
                    )
                ]
            )

        # Minimize window task
        if "minimize" in query:
            target_app = "chrome" if "chrome" in query else ("vs code" if "code" in query else None)
            return TaskPlan(
                goal=user_query,
                rationale="Minimize application window",
                steps=[
                    PlanStep(
                        id="1",
                        tool="window.minimize",
                        action=f"Minimize {target_app or 'active'} window",
                        arguments={"title_or_handle": target_app} if target_app else {},
                        expected_outcome="Window minimized"
                    )
                ]
            )

        # Maximize window task
        if "maximize" in query:
            target_app = "chrome" if "chrome" in query else ("vs code" if "code" in query else None)
            return TaskPlan(
                goal=user_query,
                rationale="Maximize application window",
                steps=[
                    PlanStep(
                        id="1",
                        tool="window.maximize",
                        action=f"Maximize {target_app or 'active'} window",
                        arguments={"title_or_handle": target_app} if target_app else {},
                        expected_outcome="Window maximized"
                    )
                ]
            )

        # Switch to window task
        if "switch" in query or "wapas jao" in query or "focus" in query:
            target = "Visual Studio Code" if ("code" in query or "vs" in query) else ("Chrome" if "chrome" in query else "Notepad")
            return TaskPlan(
                goal=user_query,
                rationale=f"Switch focus to {target}",
                steps=[
                    PlanStep(
                        id="1",
                        tool="window.focus",
                        action=f"Focus {target} window",
                        arguments={"title_or_handle": target},
                        expected_outcome=f"{target} window brought to foreground"
                    )
                ]
            )

        # Close window / app task
        if "close" in query or "band karo" in query:
            target = "chrome" if "chrome" in query else ("code" if "code" in query else None)
            if target:
                return TaskPlan(
                    goal=user_query,
                    rationale=f"Close {target} application",
                    steps=[
                        PlanStep(
                            id="1",
                            tool="computer.close_app",
                            action=f"Close {target}",
                            arguments={"app_name": target},
                            expected_outcome=f"{target} closed"
                        )
                    ]
                )
            else:
                return TaskPlan(
                    goal=user_query,
                    rationale="Close active window",
                    steps=[
                        PlanStep(
                            id="1",
                            tool="window.close",
                            action="Close active window",
                            arguments={},
                            expected_outcome="Active window closed"
                        )
                    ]
                )

        # VS Code demo task
        if "vs code" in query or "code" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Launch Visual Studio Code and verify window",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.open_app",
                        action="Launch Visual Studio Code",
                        arguments={"app_name": "code"},
                        expected_outcome="VS Code launched and verified"
                    ),
                    PlanStep(
                        id="2",
                        tool="computer.active_window",
                        action="Verify active window belongs to VS Code",
                        arguments={},
                        expected_outcome="Active window is VS Code"
                    )
                ]
            )

        # Downloads folder task
        if "downloads" in query or "download" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Open Downloads directory in File Explorer",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.open_folder",
                        action="Open Downloads folder",
                        arguments={"folder_name": "downloads"},
                        expected_outcome="Downloads folder opened in Explorer"
                    )
                ]
            )

        # Find PDF files task
        if "pdf" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Search filesystem for PDF files",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.find_files",
                        action="Find PDF files",
                        arguments={"pattern": "*.pdf", "limit": 10},
                        expected_outcome="List of PDF files found"
                    )
                ]
            )

        # Type text task
        if "type" in query or "likho" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Type text into active focus",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.type",
                        action="Type text",
                        arguments={"text": "Hello from SHIVANI!"},
                        expected_outcome="Text typed successfully"
                    )
                ]
            )

        # Chrome demo task
        if "chrome" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Launch Google Chrome browser and verify window presence",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.open_app",
                        action="Launch Google Chrome",
                        arguments={"app_name": "chrome.exe"},
                        expected_outcome="Chrome process detected in system table"
                    ),
                    PlanStep(
                        id="2",
                        tool="computer.active_window",
                        action="Verify active window belongs to Chrome",
                        arguments={},
                        expected_outcome="Active window contains Chrome"
                    )
                ]
            )

        # Notepad demo task
        if "notepad" in query or "note" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Launch Notepad application and verify presence",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.open_app",
                        action="Launch Notepad application",
                        arguments={"app_name": "notepad.exe"},
                        expected_outcome="Notepad process started"
                    ),
                    PlanStep(
                        id="2",
                        tool="computer.active_window",
                        action="Verify active window title",
                        arguments={},
                        expected_outcome="Window title contains Notepad"
                    )
                ]
            )

        # Screenshot task
        if "screenshot" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Capture desktop screenshot for observation",
                steps=[
                    PlanStep(
                        id="1",
                        tool="computer.screenshot",
                        action="Capture current screen",
                        arguments={"filename": "screen_observation.png"},
                        expected_outcome="Screenshot file created on disk"
                    )
                ]
            )

        # Filesystem list task
        if "list" in query or "files" in query or "folder" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Inspect filesystem contents",
                steps=[
                    PlanStep(
                        id="1",
                        tool="filesystem.list",
                        action="List current directory contents",
                        arguments={"path": "."},
                        expected_outcome="Directory list returned"
                    )
                ]
            )

        # Default fallback observation plan
        return TaskPlan(
            goal=user_query,
            rationale="Inspect current desktop status",
            steps=[
                PlanStep(
                    id="1",
                    tool="computer.active_window",
                    action="Inspect active foreground window",
                    arguments={},
                    expected_outcome="Active window detected"
                )
            ]
        )

    async def health_check(self) -> Dict[str, Any]:
        start = time.perf_counter()
        # Mock instantaneous ping
        latency = (time.perf_counter() - start) * 1000.0
        return {
            "healthy": True,
            "provider": "mock",
            "latency_ms": round(latency, 2),
            "status": "operational"
        }
