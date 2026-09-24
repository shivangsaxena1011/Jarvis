"""
SHIVANI Automation Registered Tools (Phase 15).
Equips the Orchestrator and Agents with tools to inspect, create, run, and manage automations.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from core.automation.engine import AutomationEngine
from security.permissions.models import RiskLevel
from tools.base import BaseTool


class AutomationListArgs(BaseModel):
    status: Optional[str] = Field(default=None, description="Optional status filter: 'ACTIVE', 'PAUSED', 'DISABLED'")


class AutomationListTool(BaseTool):
    name = "automation.list"
    description = "List all registered automations, schedules, and routines."
    permission_level = RiskLevel.SAFE
    args_schema = AutomationListArgs

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    async def run(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        automations = self.engine.list_automations()
        if status:
            automations = [a for a in automations if a.status.value.upper() == status.upper()]
        return [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description,
                "status": a.status.value,
                "enabled": a.enabled,
                "last_run": a.last_run,
                "next_run": a.next_run,
                "run_count": a.run_count,
            }
            for a in automations
        ]


class AutomationCreatePromptArgs(BaseModel):
    prompt: str = Field(description="Natural language instruction for the automation, e.g. 'Every weekday at 8 AM summarize my unread emails'")


class AutomationCreateTool(BaseTool):
    name = "automation.create"
    description = "Create a scheduled, recurring, or event-driven automation from natural language."
    permission_level = RiskLevel.LOW_RISK
    args_schema = AutomationCreatePromptArgs

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    async def run(self, prompt: str) -> Dict[str, Any]:
        auto = self.engine.create_from_prompt(prompt)
        preview = self.engine.preview_automation(auto)
        return {
            "success": True,
            "id": auto.id,
            "name": auto.name,
            "preview": preview,
        }


class AutomationRunNowArgs(BaseModel):
    automation_id: str = Field(description="ID of the automation to trigger immediately")


class AutomationRunTool(BaseTool):
    name = "automation.run"
    description = "Trigger and execute an automation workflow immediately."
    permission_level = RiskLevel.LOW_RISK
    args_schema = AutomationRunNowArgs

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    async def run(self, automation_id: str) -> Dict[str, Any]:
        run = await self.engine.run_automation_now(automation_id)
        if not run:
            return {"success": False, "error": f"Automation '{automation_id}' not found."}
        return {
            "success": run.status.value == "COMPLETED",
            "run_id": run.id,
            "status": run.status.value,
            "result": run.result,
        }


class AutomationToggleArgs(BaseModel):
    automation_id: str = Field(description="ID of the automation to pause or resume")


class AutomationPauseTool(BaseTool):
    name = "automation.pause"
    description = "Pause an active automation."
    permission_level = RiskLevel.LOW_RISK
    args_schema = AutomationToggleArgs

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    async def run(self, automation_id: str) -> Dict[str, Any]:
        ok = self.engine.pause_automation(automation_id)
        return {"success": ok, "automation_id": automation_id, "status": "PAUSED"}


class AutomationResumeTool(BaseTool):
    name = "automation.resume"
    description = "Resume a paused automation."
    permission_level = RiskLevel.LOW_RISK
    args_schema = AutomationToggleArgs

    def __init__(self, engine: AutomationEngine):
        super().__init__()
        self.engine = engine

    async def run(self, automation_id: str) -> Dict[str, Any]:
        ok = self.engine.resume_automation(automation_id)
        return {"success": ok, "automation_id": automation_id, "status": "ACTIVE"}
