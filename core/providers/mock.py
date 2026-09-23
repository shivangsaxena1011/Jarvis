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
