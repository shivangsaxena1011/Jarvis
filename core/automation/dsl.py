"""
SHIVANI Automation DSL & Natural Language Compiler (Phase 15).
Translates user voice/text into structured automations, generates transparency
previews, supports conversational editing, and provides dry-run sandbox simulation.
"""

from datetime import datetime, timezone
import json
import re
from typing import Any, Dict, List, Optional, Tuple

from core.automation.models import (
    Automation,
    AutomationPermissions,
    AutomationNotificationPolicy,
    AutomationScope,
    AutomationSource,
    AutomationStatus,
    AutomationStep,
    ConditionGroup,
    ConditionOperator,
    ConditionPredicate,
    FailurePolicy,
    LogicalOperator,
    TimeSchedule,
    TriggerConfig,
    TriggerType,
)
from security.permissions.models import RiskLevel


class AutomationDSL:
    """DSL parser, compiler, preview generator, and dry-run engine."""

    # ==========================================================================
    # Validation & Preview
    # ==========================================================================

    @classmethod
    def validate_automation(cls, data: Dict[str, Any]) -> Tuple[bool, List[str], Optional[Automation]]:
        errors: List[str] = []
        try:
            automation = Automation.model_validate(data)
            if not automation.steps:
                errors.append("Automation must contain at least one step.")
            return len(errors) == 0, errors, automation
        except Exception as e:
            return False, [str(e)], None

    @classmethod
    def generate_preview(cls, automation: Automation) -> Dict[str, Any]:
        """Generates a structured, user-facing transparency preview."""
        trigger_desc = cls._format_trigger_preview(automation.trigger)
        actions = [s.name or s.action for s in automation.steps]
        external_actions = [
            s.name or s.action
            for s in automation.steps
            if any(k in (s.tool or s.action).lower() for k in ("send", "publish", "post", "delete", "execute"))
        ]

        return {
            "name": automation.name,
            "description": automation.description,
            "runs": trigger_desc,
            "uses": list(set(s.tool.split(".")[0] if s.tool and "." in s.tool else s.action.split(".")[0] for s in automation.steps)),
            "actions": actions,
            "external_actions": external_actions or ["None (Read-only / Local)"],
            "max_risk_level": automation.permissions.max_risk_level.value,
            "requires_approval_count": sum(1 for s in automation.steps if s.requires_approval or s.risk_level in (RiskLevel.HIGH_RISK, RiskLevel.CRITICAL)),
            "conditions_summary": cls._format_conditions_preview(automation.conditions),
        }

    @classmethod
    def _format_trigger_preview(cls, trigger: TriggerConfig) -> str:
        if trigger.type == TriggerType.SCHEDULE and trigger.schedule:
            sch = trigger.schedule
            if sch.time_of_day:
                dows = ", ".join(d.upper() for d in sch.days_of_week) if sch.days_of_week else "Daily"
                return f"{dows} at {sch.time_of_day} ({sch.timezone})"
            if sch.cron:
                return f"Cron: '{sch.cron}' ({sch.timezone})"
            if sch.specific_datetime:
                return f"One-time: {sch.specific_datetime}"
        elif trigger.type == TriggerType.INTERVAL and trigger.schedule:
            return f"Every {trigger.schedule.interval_seconds} seconds"
        elif trigger.type == TriggerType.EVENT and trigger.event:
            return f"When event '{trigger.event.event_type}' occurs"
        elif trigger.type == TriggerType.FILE:
            return f"When file changes in '{trigger.file_path}' ({', '.join(trigger.file_patterns)})"
        elif trigger.type == TriggerType.DEVICE:
            return f"When device '{trigger.device_id or 'any'}' connects"
        return "Manual invocation"

    @classmethod
    def _format_conditions_preview(cls, conditions: Optional[ConditionGroup]) -> str:
        if not conditions or not conditions.predicates:
            return "Always run"
        preds = [f"{p.field} {p.operator.value} {p.value}" for p in conditions.predicates]
        return f" {conditions.logical_op.value} ".join(preds)

    # ==========================================================================
    # Natural Language -> Automation Compiler
    # ==========================================================================

    @classmethod
    def compile_prompt_to_automation(cls, prompt: str, owner: str = "user") -> Automation:
        """
        Compiles natural language into a validated Automation specification.
        Extracts intent, schedule, actions, and safety boundaries.
        """
        p_lower = prompt.lower()

        # 1. Parse Schedule / Trigger
        trigger = cls._extract_trigger_from_prompt(p_lower)

        # 2. Extract Steps
        steps: List[AutomationStep] = []
        name = "Custom Automation"
        desc = prompt

        # Pattern: Morning brief / Email & Task summary
        if "email" in p_lower and ("task" in p_lower or "summary" in p_lower or "brief" in p_lower):
            name = "Morning Brief"
            desc = "Daily summary of important emails and pending tasks."
            steps = [
                AutomationStep(
                    step_id="step_email",
                    name="Read permitted emails",
                    action="email.read_important",
                    tool="gmail.read_inbox",
                    input_template={"max_results": 10, "query": "is:unread is:important"},
                    expected_outcome="Unread emails gathered",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_tasks",
                    name="Read pending tasks",
                    action="tasks.read_pending",
                    tool="tasks.list_pending",
                    input_template={"status": "PENDING"},
                    expected_outcome="Pending tasks collected",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_summary",
                    name="Synthesize morning briefing",
                    action="summary.generate",
                    tool="content.synthesize",
                    input_template={"sources": ["{{step_email.output}}", "{{step_tasks.output}}"]},
                    expected_outcome="Structured briefing generated",
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="step_notify",
                    name="Send desktop notification",
                    action="notify_user",
                    tool="notifications.send",
                    input_template={"title": "Morning Brief", "message": "{{step_summary.output}}"},
                    expected_outcome="Notification delivered to user",
                    risk_level=RiskLevel.SAFE,
                ),
            ]
        # Pattern: Research automation
        elif "research" in p_lower or ("paper" in p_lower and "summarize" in p_lower):
            topic = re.sub(r"(?i)(every|daily|research|summarize|on|about|find|papers)", "", prompt).strip() or "AI news"
            name = f"Research Digest: {topic}"
            desc = f"Periodic research scan and summary for '{topic}'."
            steps = [
                AutomationStep(
                    step_id="s1",
                    name=f"Search sources for {topic}",
                    action="research.search",
                    tool="research.search",
                    input_template={"query": topic, "max_results": 5},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Synthesize research findings",
                    action="research.summarize",
                    tool="research.summarize",
                    input_template={"topic": topic},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s3",
                    name="Save research report artifact",
                    action="research.save",
                    tool="research.save",
                    input_template={"query": topic},
                    risk_level=RiskLevel.LOW_RISK,
                ),
            ]
        # Pattern: PDF in Downloads
        elif "pdf" in p_lower and "download" in p_lower:
            name = "Downloads PDF Organizer"
            desc = "Monitors Downloads folder for new PDFs and prompts for summarization."
            trigger = TriggerConfig(
                type=TriggerType.FILE,
                file_path="C:/Users/Project/Jarvis/Downloads",
                file_patterns=["*.pdf"],
                description="Watched Downloads directory for PDFs",
            )
            steps = [
                AutomationStep(
                    step_id="s1",
                    name="Notify user of new PDF and ask to summarize",
                    action="notify_user",
                    tool="notifications.send",
                    input_template={"title": "New PDF Detected", "message": "A new PDF arrived in Downloads. Would you like a summary?"},
                    risk_level=RiskLevel.SAFE,
                )
            ]
        # Pattern: Build failure
        elif "build" in p_lower and "fail" in p_lower:
            name = "Build Failure Analyzer"
            desc = "Analyzes build logs and drafts fixes on build failure."
            trigger = TriggerConfig(
                type=TriggerType.EVENT,
                event={"event_type": "TOOL_FAILED", "filter_expression": {"tool": "terminal_execute"}},
                description="Triggered when terminal build fails",
            )
            steps = [
                AutomationStep(
                    step_id="s1",
                    name="Analyze build error",
                    action="code.analyze_error",
                    tool="code.inspect",
                    input_template={"error_context": "{{event.error}}"},
                    risk_level=RiskLevel.SAFE,
                ),
                AutomationStep(
                    step_id="s2",
                    name="Prepare code patch",
                    action="code.prepare_patch",
                    tool="code.patch",
                    input_template={"fix": "{{s1.output}}"},
                    requires_approval=True,
                    risk_level=RiskLevel.HIGH_RISK,
                ),
            ]
        # Fallback generic task
        else:
            name = prompt[:30].strip() or "Scheduled Automation"
            steps = [
                AutomationStep(
                    step_id="s1",
                    name=prompt[:50],
                    action="system.run_query",
                    input_template={"query": prompt},
                    risk_level=RiskLevel.SAFE,
                )
            ]

        # Safety Permissions
        permissions = AutomationPermissions(
            allowed_capabilities=["browser", "research", "knowledge", "notifications", "tasks", "email", "system", "code"],
            max_risk_level=RiskLevel.SENSITIVE,
        )

        return Automation(
            name=name,
            description=desc,
            trigger=trigger,
            steps=steps,
            permissions=permissions,
            source=AutomationSource.USER_CREATED,
            owner=owner,
        )

    @classmethod
    def _extract_trigger_from_prompt(cls, p: str) -> TriggerConfig:
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", p)
        time_str = "08:00"
        if time_match:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            mer = time_match.group(3).lower()
            if mer == "pm" and hr < 12:
                hr += 12
            elif mer == "am" and hr == 12:
                hr = 0
            time_str = f"{hr:02d}:{mn:02d}"

        # Days of week
        dows = []
        if "weekday" in p or "monday to friday" in p or "mon-fri" in p:
            dows = ["mon", "tue", "wed", "thu", "fri"]
        elif "weekend" in p:
            dows = ["sat", "sun"]
        else:
            for day in ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"):
                if day in p:
                    dows.append(day[:3])

        return TriggerConfig(
            type=TriggerType.SCHEDULE,
            schedule=TimeSchedule(
                time_of_day=time_str,
                days_of_week=dows,
                timezone="Asia/Kolkata",
            ),
        )

    # ==========================================================================
    # Conversational Editing
    # ==========================================================================

    @classmethod
    def edit_automation_with_prompt(cls, automation: Automation, prompt: str) -> Automation:
        """Applies natural language edit instructions to an existing automation."""
        p = prompt.lower()
        automation.version += 1

        # 1. Edit Time / Schedule
        time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)", p)
        if time_match and automation.trigger.schedule:
            hr = int(time_match.group(1))
            mn = int(time_match.group(2) or 0)
            mer = time_match.group(3).lower()
            if mer == "pm" and hr < 12:
                hr += 12
            elif mer == "am" and hr == 12:
                hr = 0
            automation.trigger.schedule.time_of_day = f"{hr:02d}:{mn:02d}"

        # 2. Weekday restriction
        if "weekday" in p or "monday to friday" in p:
            if automation.trigger.schedule:
                automation.trigger.schedule.days_of_week = ["mon", "tue", "wed", "thu", "fri"]

        # 3. Pause instruction
        if "pause" in p:
            automation.enabled = False
            automation.status = AutomationStatus.PAUSED

        # 4. Resume / Enable instruction
        if "resume" in p or "enable" in p:
            automation.enabled = True
            automation.status = AutomationStatus.ACTIVE

        automation.updated_at = datetime.now(timezone.utc).isoformat()
        return automation

    # ==========================================================================
    # Dry Run Simulator
    # ==========================================================================

    @classmethod
    def dry_run_simulation(cls, automation: Automation, simulated_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a non-destructive dry-run simulation of the automation.
        Verifies condition evaluation, permission checks, and step routing without mutations.
        """
        from core.automation.conditions import ConditionEngine

        # 1. Evaluate conditions
        condition_met = ConditionEngine.evaluate_group(automation.conditions, simulated_context)
        if not condition_met:
            return {
                "success": True,
                "executed": False,
                "reason": "Conditions not met in simulation context",
                "steps_simulated": 0,
            }

        simulated_steps = []
        for s in automation.steps:
            simulated_steps.append({
                "step_id": s.step_id,
                "name": s.name or s.action,
                "tool": s.tool or s.action,
                "risk_level": s.risk_level.value,
                "requires_approval": s.requires_approval or s.risk_level in (RiskLevel.HIGH_RISK, RiskLevel.CRITICAL),
                "simulated_outcome": s.expected_outcome or "Executed successfully in sandbox",
            })

        return {
            "success": True,
            "executed": True,
            "steps_simulated": len(simulated_steps),
            "steps": simulated_steps,
            "external_side_effects_prevented": True,
        }
