"""
SHIVANI Mock LLM Provider
Deterministic model provider used for unit testing, offline development,
and predictable regression tests without external API dependencies.
"""

from typing import Any, Dict, List, Optional
from core.llm.base import LLMProvider, TaskPlan, PlanStep


class MockLLMProvider(LLMProvider):
    def __init__(self, canned_plans: Optional[Dict[str, TaskPlan]] = None):
        self.canned_plans = canned_plans or {}

    async def generate_text(
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
        return "Understood. Ready to proceed."

    async def generate_plan(
        self,
        user_query: str,
        available_tools: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPlan:
        query = user_query.lower().strip()

        # Check if pre-registered canned plan exists
        for key, plan in self.canned_plans.items():
            if key in query:
                return plan

        # Heuristic planning for mock tests
        if "notepad" in query or "note" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Open application notepad and verify it launched.",
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
                        tool="computer.get_active_window",
                        action="Verify active window title",
                        arguments={},
                        expected_outcome="Window title contains Notepad"
                    )
                ]
            )

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

        if "list files" in query or "files" in query or "folder" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Inspect filesystem contents",
                steps=[
                    PlanStep(
                        id="1",
                        tool="filesystem.list_dir",
                        action="List current directory contents",
                        arguments={"path": "."},
                        expected_outcome="Directory list returned"
                    )
                ]
            )

        if "delete" in query or "clean" in query:
            return TaskPlan(
                goal=user_query,
                rationale="Delete specified files with explicit confirmation",
                steps=[
                    PlanStep(
                        id="1",
                        tool="filesystem.safe_delete",
                        action="Delete target file safely",
                        arguments={"path": "temp_to_delete.txt"},
                        requires_confirmation=True,
                        expected_outcome="File removed"
                    )
                ]
            )

        # Default single inspection step
        return TaskPlan(
            goal=user_query,
            rationale="Default state observation",
            steps=[
                PlanStep(
                    id="1",
                    tool="computer.get_active_window",
                    action="Check current desktop state",
                    arguments={},
                    expected_outcome="Active window detected"
                )
            ]
        )
