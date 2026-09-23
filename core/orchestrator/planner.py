"""
SHIVANI Task Planner
Decomposes user requests into structured, verified multi-step execution plans.
"""

from typing import Any, Dict, List, Optional
from core.llm.base import LLMProvider, TaskPlan
from tools.registry import ToolRegistry
from core.context.normalizer import SessionContext


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

        # Prefer normalized query for LLM reasoning if different
        effective_query = normalized_query if normalized_query else query
        
        plan = await self.llm.generate_plan(
            user_query=effective_query,
            available_tools=available_tools,
            context=ctx_dict
        )

        return plan
