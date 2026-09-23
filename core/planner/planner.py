"""
SHIVANI Task Planner
Decomposes user requests into verified multi-step execution plans,
classifies risk tiers, and evaluates confirmation requirements.
"""

from typing import Any, Dict, List, Optional
from core.providers.base import LLMProvider
from core.tasks.task import TaskPlan, PlanStep
from tools.registry import ToolRegistry
from core.context.normalizer import SessionContext
from security.permissions.engine import RiskLevel


class TaskPlanner:
    def __init__(self, llm_provider: LLMProvider, tool_registry: ToolRegistry):
        self.llm = llm_provider
        self.tools = tool_registry

    async def create_plan(
        self,
        query: str,
        normalized_query: str,
        context: Optional[SessionContext] = None
    ) -> TaskPlan:
        available_tools = self.tools.list_tools()
        ctx_dict = context.model_dump() if context else {}
        effective_query = normalized_query if normalized_query else query

        # Delegate plan generation to configured LLMProvider
        plan = await self.llm.generate_plan(
            user_query=effective_query,
            available_tools=available_tools,
            context=ctx_dict
        )

        # Post-process steps: sync confirmation requirements and risk levels
        for step in plan.steps:
            tool = self.tools.get_tool(step.tool)
            if tool:
                # If tool is SENSITIVE or CRITICAL, enforce confirmation requirement
                if tool.permission_level in (RiskLevel.SENSITIVE, RiskLevel.CRITICAL):
                    step.requires_confirmation = True

        return plan
