"""
SHIVANI Computer Autonomy Tools (Phase 17).
Exposes closed-loop desktop observation, action execution,
emergency stop, and manual takeover to the Tool Registry and Orchestrator.
"""

from typing import Any, Dict, List, Optional
from core.computer.agent import ComputerAutonomyAgent
from core.computer.models import ActionType, ComputerAction
from tools.base import BaseTool, ToolResult
from security.permissions.engine import RiskLevel

# Shared singleton agent instance
_computer_agent: Optional[ComputerAutonomyAgent] = None


def get_computer_autonomy_agent() -> ComputerAutonomyAgent:
    global _computer_agent
    if _computer_agent is None:
        _computer_agent = ComputerAutonomyAgent()
    return _computer_agent


class ComputerObserveTool(BaseTool):
    name = "computer.observe"
    description = "Captures the current desktop observation including active window, monitors, and UI elements."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, capture_image: bool = False, **kwargs: Any) -> ToolResult:
        agent = get_computer_autonomy_agent()
        obs = await agent.observe(capture_image=capture_image)
        return ToolResult(
            success=True,
            data={
                "active_window": obs.active_window,
                "element_count": len(obs.elements),
                "monitors": [m.model_dump() for m in obs.monitors],
                "application": obs.application_context.model_dump(),
                "top_elements": [e.model_dump() for e in obs.elements[:15]],
            },
        )


class ComputerActTool(BaseTool):
    name = "computer.act"
    description = "Executes a closed-loop computer action (click, type, hotkey, open, etc.) with outcome verification."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(
        self,
        action_type: str,
        target: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        expected_state: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> ToolResult:
        agent = get_computer_autonomy_agent()
        atype = ActionType(action_type.lower())
        action = ComputerAction(
            action_type=atype,
            target=target,
            parameters=parameters or {},
            expected_state=expected_state or {},
        )
        res = await agent.execute_action(action)
        return ToolResult(
            success=res.verified,
            data=res.model_dump(),
            error=res.failure_reason,
        )


class ComputerStopTool(BaseTool):
    name = "computer.stop"
    description = "Immediately halts running computer actions, activates emergency stop, and locks resources."
    permission_level: RiskLevel = RiskLevel.SAFE

    async def run(self, **kwargs: Any) -> ToolResult:
        agent = get_computer_autonomy_agent()
        agent.emergency_stop()
        return ToolResult(
            success=True,
            data={"emergency_stopped": True, "message": "Emergency stop invoked. All actions halted."},
        )


def register_computer_autonomy_tools(registry: Any) -> None:
    """Registers Phase 17 computer autonomy tools into the system tool registry."""
    registry.register(ComputerObserveTool())
    registry.register(ComputerActTool())
    registry.register(ComputerStopTool())
