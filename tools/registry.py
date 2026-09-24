"""
SHIVANI Tool Registry
Manages tool discovery, permission evaluation, execution timeout, verification,
and audit logging.
"""

import time
import asyncio
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from tools.base import BaseTool, ToolResult
from security.permissions.engine import PermissionEngine, RiskLevel
from security.audit.logger import AuditLogger


class ToolRegistry:
    def __init__(
        self,
        permission_engine: Optional[PermissionEngine] = None,
        audit_logger: Optional[AuditLogger] = None
    ):
        self._tools: Dict[str, BaseTool] = {}
        self.permissions = permission_engine or PermissionEngine()
        self.audit = audit_logger or AuditLogger()

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool
        # Sync risk level with permission engine
        self.permissions.set_tool_risk(tool.name, tool.permission_level)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        return [tool.get_metadata() for tool in self._tools.values()]

    async def execute_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        task_id: str = "adhoc",
        timeout_override: Optional[float] = None
    ) -> ToolResult:
        tool = self.get_tool(name)
        if not tool:
            err = f"Tool '{name}' is not registered."
            self.audit.log_event("tool_not_found", task_id=task_id, tool_name=name, success=False, error=err)
            return ToolResult(success=False, error=err)

        # 1. Validate Arguments
        validated_args = arguments
        if tool.args_schema:
            try:
                validated = tool.args_schema(**arguments)
                validated_args = validated.model_dump()
            except ValidationError as ve:
                err = f"Argument validation failed: {ve}"
                self.audit.log_event("tool_invalid_args", task_id=task_id, tool_name=name, details={"args": arguments}, success=False, error=err)
                return ToolResult(success=False, error=err)

        # 2. Command Security Validation
        if "command" in validated_args and isinstance(validated_args["command"], str):
            from security.sandbox.command_validator import CommandValidator
            is_blocked, reason = CommandValidator.is_blocked(validated_args["command"])
            if is_blocked:
                err = f"Security Sandbox Violation: Blocked dangerous command: {reason}"
                self.audit.log_event("command_blocked", task_id=task_id, tool_name=name, details={"command": validated_args["command"]}, success=False, error=err)
                return ToolResult(success=False, error=err)


        # 3. Safe Mode & Demo Mode
        import os
        if os.getenv("SHIVANI_SAFE_MODE", "0").lower() in ("1", "true", "yes"):
            from core.modes import SafeModeController
            safe = SafeModeController(enabled=True)
            try:
                safe.validate_tool_execution(name, tool.permission_level)
            except Exception as se:
                err = str(se)
                self.audit.log_event("safe_mode_blocked", task_id=task_id, tool_name=name, success=False, error=err)
                return ToolResult(success=False, error=err)

        if os.getenv("SHIVANI_DEMO_MODE", "0").lower() in ("1", "true", "yes"):
            from core.modes import DemoModeController
            demo = DemoModeController(enabled=True)
            sim_data = demo.simulate_execution(name, validated_args)
            return ToolResult(success=True, data=sim_data, verification={"verified": True, "demo": True})

        # 4. Permission Check & User Approval
        authorized = await self.permissions.evaluate_and_request(
            task_id=task_id,
            tool_name=name,
            arguments=validated_args,
            default_risk=tool.permission_level,
            description=f"Execute {name}",
            target=str(validated_args.get("path") or validated_args.get("app_name") or validated_args.get("command") or "")
        )
        if not authorized:
            err = f"Execution of tool '{name}' was rejected or timed out by permission policy."
            self.audit.log_event("tool_permission_denied", task_id=task_id, tool_name=name, success=False, error=err)
            return ToolResult(success=False, error=err)

        # 5. Execution with Timeout & Retries
        from observability.metrics import METRICS
        METRICS.increment("tool.calls", tags={"tool": name})

        timeout_sec = timeout_override or tool.timeout
        attempts = max(1, tool.retry_policy)
        last_error = None
        start_time = time.perf_counter()

        for attempt in range(1, attempts + 1):
            try:
                raw_data = await asyncio.wait_for(tool.run(**validated_args), timeout=timeout_sec)
                
                # Verification Check
                verification = await tool.verify(raw_data, **validated_args)
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0

                is_verified = verification.get("verified", True)
                if not is_verified:
                    last_error = f"Verification failed: {verification.get('error', 'unknown issue')}"
                    continue

                res = ToolResult(
                    success=True,
                    data=raw_data,
                    verification=verification,
                    execution_time_ms=elapsed_ms
                )
                METRICS.increment("tool.success", tags={"tool": name})
                METRICS.record_latency(f"tool.{name}", elapsed_ms / 1000.0)
                self.audit.log_event("tool_executed", task_id=task_id, tool_name=name, details={"args": validated_args, "verification": verification}, success=True)
                return res

            except asyncio.TimeoutError:
                last_error = f"Tool execution timed out after {timeout_sec}s."
            except Exception as e:
                last_error = str(e)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        METRICS.increment("tool.failure", tags={"tool": name})
        self.audit.log_event("tool_failed", task_id=task_id, tool_name=name, details={"args": validated_args}, success=False, error=last_error)
        return ToolResult(success=False, error=last_error, execution_time_ms=elapsed_ms)

