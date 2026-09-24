"""
SHIVANI Cross-Application Workflow Engine
Orchestrates multi-agent, cross-tool workflows with variable passing,
pausing at approval gates, resuming without restarting, and rich failure diagnostics.
"""

import time
import copy
from typing import Any, Callable, Dict, List, Optional
from pathlib import Path

from core.workflows.models import Workflow, WorkflowStep, WorkflowStatus, WorkflowResult
from tools.registry import ToolRegistry
from security.permissions.engine import PermissionEngine, RiskLevel
from core.events.bus import EventBus, EventType, get_event_bus
from agents.browser.agent import BrowserAgent
from tools.desktop.os import OperatingSystemAdapter, get_os_adapter


class WorkflowEngine:
    """Master runtime for executing, pausing, and resuming cross-application workflows."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        permission_engine: Optional[PermissionEngine] = None,
        event_bus: Optional[EventBus] = None,
        browser_agent: Optional[BrowserAgent] = None,
        os_adapter: Optional[OperatingSystemAdapter] = None
    ):
        self.tools = tool_registry
        self.permissions = permission_engine or PermissionEngine()
        self.events = event_bus or get_event_bus()
        self.browser = browser_agent
        self.os_adapter = os_adapter or get_os_adapter()
        self._workflows: Dict[str, Workflow] = {}

    def register_workflow(self, workflow: Workflow) -> None:
        self._workflows[workflow.id] = workflow

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self._workflows.get(workflow_id)

    async def execute_workflow(
        self,
        workflow: Workflow,
        on_step_callback: Optional[Callable[[Workflow, WorkflowStep], None]] = None
    ) -> WorkflowResult:
        """Executes workflow from current_step_index until completion or approval pause."""
        self.register_workflow(workflow)
        workflow.status = WorkflowStatus.RUNNING
        self.events.publish(EventType.TASK_STARTED, task_id=workflow.id, data={"workflow": workflow.name})

        while workflow.current_step_index < len(workflow.steps):
            step = workflow.steps[workflow.current_step_index]
            step.status = "RUNNING"

            if on_step_callback:
                on_step_callback(workflow, step)

            # 1. Resolve dynamic inputs from workflow context_data
            resolved_inputs = self._resolve_template_inputs(step.input, workflow.context_data)

            # 2. Check for Approval Requirement
            is_policy_sensitive = step.permission in (RiskLevel.SENSITIVE, RiskLevel.CRITICAL) and self.permissions.policy == "strict"
            if (step.requires_approval or is_policy_sensitive) and not step.verification.get("user_approved"):
                workflow.status = WorkflowStatus.WAITING_FOR_APPROVAL
                req = self.permissions.request_approval(
                    task_id=workflow.id,
                    tool_name=step.tool,
                    arguments=resolved_inputs,
                    description=step.description,
                    risk_level=step.permission
                )
                workflow.pending_approval_id = req.id
                self.events.publish(
                    EventType.TASK_WAITING_APPROVAL,
                    task_id=workflow.id,
                    data={"step_id": step.id, "approval_id": req.id, "description": step.description}
                )
                return self._build_result(
                    workflow,
                    success=False,
                    message=f"Workflow paused at step {workflow.current_step_index + 1}: '{step.description}'. Waiting for user approval."
                )

            # 3. Execute Step Tool
            start_time = time.perf_counter()
            self.events.publish(EventType.TOOL_STARTED, task_id=workflow.id, data={"tool": step.tool, "step_id": step.id})

            tool_res = await self.tools.execute_tool(
                name=step.tool,
                arguments=resolved_inputs,
                task_id=workflow.id
            )
            if hasattr(self.permissions, "revoke_preapproval"):
                self.permissions.revoke_preapproval(workflow.id, step.tool)
            exec_time = (time.perf_counter() - start_time) * 1000.0

            step.execution_time_ms = round(exec_time, 2)
            step.result = tool_res.data
            step.verification = tool_res.verification or {}
            step.error = tool_res.error

            if not tool_res.success:
                step.status = "FAILED"
                workflow.status = WorkflowStatus.FAILED
                workflow.error = f"Step '{step.description}' failed: {tool_res.error}"
                
                # Gather failure diagnostics
                diagnostics = await self._capture_diagnostics()
                workflow.failure_diagnostics = diagnostics
                
                self.events.publish(EventType.TOOL_FAILED, task_id=workflow.id, data={"error": tool_res.error, "diagnostics": diagnostics})
                return self._build_result(workflow, success=False, message=workflow.error)

            # Step Succeeded
            step.status = "COMPLETED"
            self.events.publish(EventType.TOOL_COMPLETED, task_id=workflow.id, data={"step_id": step.id})

            # Update context_data with step results for subsequent steps
            self._update_workflow_context(workflow, step)
            workflow.current_step_index += 1

        # All steps completed
        workflow.status = WorkflowStatus.COMPLETED
        self.events.publish(EventType.TASK_COMPLETED, task_id=workflow.id, data={"workflow": workflow.name})
        return self._build_result(workflow, success=True, message=f"Workflow '{workflow.name}' completed successfully.")

    async def resume_workflow(self, workflow_id: str, approved: bool = True) -> WorkflowResult:
        """Resumes a paused workflow without restarting from the beginning."""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow '{workflow_id}' not found.")

        if workflow.status != WorkflowStatus.WAITING_FOR_APPROVAL:
            return self._build_result(workflow, success=False, message=f"Workflow is not waiting for approval (current state: {workflow.status.value}).")

        if not approved:
            workflow.status = WorkflowStatus.CANCELLED
            workflow.error = "User declined approval for paused step."
            if workflow.pending_approval_id:
                self.permissions.resolve_request(workflow.pending_approval_id, False, resolved_by="user")
            return self._build_result(workflow, success=False, message="Workflow cancelled by user.")

        # Mark step approved
        current_step = workflow.steps[workflow.current_step_index]
        current_step.verification["user_approved"] = True
        if hasattr(self.permissions, "grant_preapproval"):
            self.permissions.grant_preapproval(workflow.id, current_step.tool)
        if workflow.pending_approval_id:
            self.permissions.resolve_request(workflow.pending_approval_id, True, resolved_by="user")
            workflow.pending_approval_id = None

        # Continue execution from current step
        return await self.execute_workflow(workflow)

    def _resolve_template_inputs(self, raw_input: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Substitutes placeholders like '{project.path}' or '{draft_id}' with context values."""
        resolved = copy.deepcopy(raw_input)
        for key, val in resolved.items():
            if isinstance(val, str) and "{" in val and "}" in val:
                for ctx_k, ctx_v in context.items():
                    placeholder = f"{{{ctx_k}}}"
                    if placeholder in val:
                        val = val.replace(placeholder, str(ctx_v))
                resolved[key] = val
        return resolved

    def _update_workflow_context(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Injects step result fields into workflow.context_data."""
        res = step.result
        if isinstance(res, dict):
            for k, v in res.items():
                workflow.context_data[k] = v
                workflow.context_data[f"{step.id}.{k}"] = v
        elif res is not None:
            workflow.context_data[step.id] = res

    async def _capture_diagnostics(self) -> Dict[str, Any]:
        """Captures active environmental snapshot on step failure."""
        diagnostics = {}
        try:
            active_win = await self.os_adapter.get_active_window()
            if active_win:
                diagnostics["active_window"] = active_win.title
        except Exception:
            pass

        if self.browser:
            try:
                page = await self.browser.get_active_page()
                diagnostics["browser_url"] = page.url
                diagnostics["browser_title"] = await page.title()
            except Exception:
                pass

        return diagnostics

    def _build_result(self, workflow: Workflow, success: bool, message: str) -> WorkflowResult:
        step_summaries = []
        for s in workflow.steps:
            step_summaries.append({
                "id": s.id,
                "description": s.description,
                "tool": s.tool,
                "status": s.status,
                "verification": s.verification,
                "error": s.error
            })

        return WorkflowResult(
            workflow_id=workflow.id,
            workflow_name=workflow.name,
            success=success,
            status=workflow.status,
            current_step=workflow.current_step_index,
            total_steps=len(workflow.steps),
            step_results=step_summaries,
            final_data=workflow.context_data,
            pending_approval_id=workflow.pending_approval_id,
            error=workflow.error,
            message=message
        )
