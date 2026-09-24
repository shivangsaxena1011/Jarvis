"""
SHIVANI Automation Runner & Execution Engine (Phase 15).
Executes automation workflows with step-by-step verification, idempotency guards,
exponential backoff retries, human approval pauses, and failure policy enforcement.
"""

import asyncio
from datetime import datetime, time, timezone
import hashlib
import json
import logging
import time as time_mod
from typing import Any, Callable, Dict, List, Optional

from core.automation.conditions import ConditionEngine
from core.automation.models import (
    Automation,
    AutomationRun,
    AutomationStep,
    FailurePolicy,
    RunStatus,
    StepRunRecord,
)
from core.automation.permissions import AutomationPermissionEvaluator, PromptInjectionDefense
from core.automation.store import AutomationStore
from core.events.bus import Event, EventBus, EventType
from notifications.center import NotificationCategory, NotificationCenter
from security.permissions.engine import PermissionEngine
from security.permissions.models import RiskLevel, ApprovalStatus

logger = logging.getLogger("shivani.automation.runner")


class AutomationRunner:
    """Executes single automation workflows with complete safety, idempotency, and recovery."""

    def __init__(
        self,
        store: AutomationStore,
        permission_engine: PermissionEngine,
        event_bus: Optional[EventBus] = None,
        notification_center: Optional[NotificationCenter] = None,
        tool_dispatcher: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ):
        self.store = store
        self.permissions = permission_engine
        self.permission_evaluator = AutomationPermissionEvaluator(permission_engine)
        self.events = event_bus
        self.notifications = notification_center
        self.tool_dispatcher = tool_dispatcher

    def is_in_quiet_hours(self, automation: Automation, now: Optional[datetime] = None) -> bool:
        policy = automation.notification_policy
        if not policy.quiet_hours_enabled:
            return False

        curr_time = (now or datetime.now(timezone.utc)).time()
        try:
            start_h, start_m = map(int, policy.quiet_hours_start.split(":"))
            end_h, end_m = map(int, policy.quiet_hours_end.split(":"))
            start_time = time(start_h, start_m)
            end_time = time(end_h, end_m)

            if start_time <= end_time:
                return start_time <= curr_time <= end_time
            else:
                # Overnight window (e.g. 23:00 to 07:00)
                return curr_time >= start_time or curr_time <= end_time
        except Exception:
            return False

    async def run_automation(
        self,
        automation: Automation,
        trigger_context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> AutomationRun:
        """Executes an automation workflow instance."""
        trigger_ctx = trigger_context or {}
        run = AutomationRun(
            automation_id=automation.id,
            automation_name=automation.name,
            trigger_context=trigger_ctx,
            status=RunStatus.RUNNING,
        )
        self.store.record_run(run)

        # 1. Condition Evaluation
        if automation.conditions:
            run.status = RunStatus.EVALUATING
            self.store.record_run(run)
            eval_ctx = {**trigger_ctx, "automation": automation.model_dump()}
            condition_met = ConditionEngine.evaluate_group(automation.conditions, eval_ctx)
            if not condition_met:
                run.status = RunStatus.SKIPPED
                run.completed_at = datetime.now(timezone.utc).isoformat()
                run.result = {"message": "Conditions evaluated to False. Workflow skipped."}
                self.store.record_run(run)
                return run

        # 2. Quiet Hours check for notifications
        in_quiet_hours = self.is_in_quiet_hours(automation)

        # Notify Start if requested
        if automation.notification_policy.notify_on_start and not in_quiet_hours and self.notifications:
            self.notifications.notify(
                title=f"Automation Started: {automation.name}",
                message=f"Executing {len(automation.steps)} steps.",
                category=NotificationCategory.INFO,
            )

        run.status = RunStatus.RUNNING
        self.store.record_run(run)

        step_context = dict(trigger_ctx)
        overall_success = True

        for step in automation.steps:
            step_record = StepRunRecord(
                step_id=step.step_id,
                name=step.name or step.action,
                tool=step.tool or step.action,
                input=step.input_template,
                status="RUNNING",
            )
            run.steps.append(step_record)
            self.store.record_run(run)

            # Untrusted Input & Prompt Injection Defense
            injection_detected = False
            injection_msg = ""
            def _scan_obj(val):
                nonlocal injection_detected, injection_msg
                if isinstance(val, str):
                    detected, pattern = PromptInjectionDefense.detect_injection_attempt(val)
                    if detected:
                        injection_detected = True
                        injection_msg = f"Prompt injection pattern detected: '{pattern}'"
                elif isinstance(val, dict):
                    for v in val.values():
                        _scan_obj(v)
                elif isinstance(val, (list, tuple)):
                    for v in val:
                        _scan_obj(v)

            _scan_obj(step.input_template)
            if injection_detected:
                step_record.status = "FAILED"
                step_record.error = f"Security Violation: {injection_msg}"
                run.errors.append(step_record.error)
                overall_success = False
                break

            # Permission Evaluation & High-Risk Gating
            allowed, requires_approval, reason = self.permission_evaluator.evaluate_step(automation, step)
            if not allowed:
                step_record.status = "FAILED"
                step_record.error = f"Security Violation: {reason}"
                run.errors.append(step_record.error)
                overall_success = False
                break

            if requires_approval and not dry_run:
                run.status = RunStatus.WAITING_FOR_PERMISSION
                self.store.record_run(run)
                approval_req = self.permissions.request_approval(
                    task_id=run.id,
                    tool_name=step.tool or step.action,
                    arguments=step.input_template,
                    description=f"Automation '{automation.name}' step: {step.name or step.action}",
                    risk_level=step.risk_level,
                )
                run.approval_events.append({
                    "request_id": approval_req.id,
                    "step_id": step.step_id,
                    "action": step.action,
                    "risk_level": step.risk_level.value,
                    "requested_at": datetime.now(timezone.utc).isoformat(),
                })
                self.store.record_run(run)

                # Wait for user resolution
                approved = await self._await_approval(approval_req.id, timeout_sec=step.timeout_seconds)
                if not approved:
                    step_record.status = "REJECTED"
                    step_record.error = "Action rejected or timed out by user."
                    run.warnings.append(step_record.error)
                    overall_success = False
                    run.status = RunStatus.FAILED
                    break

            # Idempotency Guard
            idempotency_key = step.idempotency_key or f"{automation.id}_{step.step_id}_{hashlib.sha256(json.dumps(step.input_template, sort_keys=True).encode()).hexdigest()[:16]}"
            input_hash = hashlib.sha256(json.dumps(step.input_template, sort_keys=True).encode()).hexdigest()

            is_duplicate = self.store.check_and_set_idempotency(
                key=idempotency_key,
                automation_id=automation.id,
                step_id=step.step_id,
                hash_val=input_hash,
            )
            if is_duplicate:
                logger.info(f"Duplicate step detected for key '{idempotency_key}'. Skipping execution.")
                step_record.status = "SKIPPED_DUPLICATE"
                step_record.output = {"message": "Skipped due to idempotency guard (duplicate execution detected)"}
                run.warnings.append(f"Step '{step.name}' skipped (idempotency key matched previous run)")
                continue

            # Execute Step with Retries
            step_start = time_mod.perf_counter()
            step_output = None
            step_error = None
            max_attempts = step.retry_count if step.failure_policy == FailurePolicy.RETRY else 1

            for attempt in range(max_attempts):
                try:
                    if dry_run:
                        step_output = {"simulated": True, "action": step.action}
                        step_error = None
                        break

                    # Dispatch Tool
                    step_output = await self._dispatch_step(step, step_context)
                    step_error = None
                    break
                except Exception as e:
                    step_error = str(e)
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff

            step_record.duration_ms = round((time_mod.perf_counter() - step_start) * 1000, 2)
            step_record.completed_at = datetime.now(timezone.utc).isoformat()

            if step_error:
                step_record.status = "FAILED"
                step_record.error = step_error
                run.errors.append(f"Step '{step.name}' failed: {step_error}")

                # Failure Policy handling
                if step.failure_policy == FailurePolicy.STOP or automation.failure_policy == FailurePolicy.STOP:
                    overall_success = False
                    break
                elif step.failure_policy == FailurePolicy.SKIP_STEP:
                    run.warnings.append(f"Skipping failed step '{step.name}' per policy.")
                    continue
                elif step.failure_policy == FailurePolicy.PAUSE_FOR_USER:
                    run.status = RunStatus.PAUSED
                    self.store.record_run(run)
                    return run
            else:
                step_record.status = "COMPLETED"
                step_record.output = step_output
                # Store in step context for subsequent step template resolution
                step_context[f"step_{step.step_id}_output"] = step_output
                step_context[step.step_id] = {"output": step_output}

            self.store.record_run(run)

        # Finalize Run
        run.completed_at = datetime.now(timezone.utc).isoformat()
        run.status = RunStatus.COMPLETED if overall_success else RunStatus.FAILED
        run.result = {"success": overall_success, "steps_completed": sum(1 for s in run.steps if s.status == "COMPLETED")}

        # Update Automation Stats
        automation.last_run = run.completed_at
        automation.run_count += 1
        if overall_success:
            automation.success_count += 1
        else:
            automation.failure_count += 1
        self.store.save_automation(automation)
        self.store.record_run(run)

        # Completion Notification
        if not in_quiet_hours and self.notifications:
            if overall_success and automation.notification_policy.notify_on_complete:
                self.notifications.notify(
                    title=f"Automation Completed: {automation.name}",
                    message=f"Successfully executed {len(automation.steps)} steps.",
                    category=NotificationCategory.SUCCESS,
                )
            elif not overall_success and automation.notification_policy.notify_on_failure:
                self.notifications.notify(
                    title=f"Automation Failed: {automation.name}",
                    message=f"Failed with errors: {'; '.join(run.errors[:2])}",
                    category=NotificationCategory.ERROR,
                )

        return run

    async def _await_approval(self, request_id: str, timeout_sec: float = 60.0) -> bool:
        start = time_mod.time()
        while time_mod.time() - start < timeout_sec:
            req = self.permissions.get_request(request_id)
            if not req:
                return False
            if req.status == ApprovalStatus.APPROVED:
                return True
            if req.status in (ApprovalStatus.REJECTED, ApprovalStatus.EXPIRED):
                return False
            await asyncio.sleep(0.5)
        return False

    async def _dispatch_step(self, step: AutomationStep, context: Dict[str, Any]) -> Any:
        # Prompt injection inspection on input
        for val in step.input_template.values():
            if isinstance(val, str):
                has_inj, pat = PromptInjectionDefense.detect_injection_attempt(val)
                if has_inj:
                    raise ValueError(f"Prompt injection pattern detected in input: '{pat}'")

        if self.tool_dispatcher:
            tool_name = step.tool or step.action
            res = self.tool_dispatcher(tool_name, step.input_template)
            if hasattr(res, "__await__"):
                return await res
            return res

        # Default synthetic execution if tool_dispatcher not provided
        return {"action": step.action, "status": "executed", "timestamp": datetime.now(timezone.utc).isoformat()}
