"""
SHIVANI Master Automation Engine (Phase 15).
Coordinates Registry, Persistent Store, Event Bus Subscriptions,
Time Triggers, Background Worker, and Human Approval Queues.
"""

import asyncio
from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

from core.automation.dsl import AutomationDSL
from core.automation.models import (
    Automation,
    AutomationRun,
    AutomationStatus,
    RunStatus,
    TriggerType,
)
from core.automation.runner import AutomationRunner
from core.automation.store import AutomationStore
from core.automation.templates import get_default_templates
from core.automation.triggers import EventTriggerMatcher, TimeTriggerEvaluator
from core.automation.worker import AutomationWorker
from core.events.bus import Event, EventBus, EventType
from notifications.center import NotificationCenter
from security.permissions.engine import PermissionEngine

logger = logging.getLogger("shivani.automation.engine")


class AutomationEngine:
    """Master facade for Proactive Intelligence, Routines, and Autonomous Workflows."""

    def __init__(
        self,
        db_path: Optional[Union[str, Path]] = None,
        permission_engine: Optional[PermissionEngine] = None,
        event_bus: Optional[EventBus] = None,
        notification_center: Optional[NotificationCenter] = None,
        orchestrator: Optional[Any] = None,
    ):
        self.store = AutomationStore(db_path=db_path)
        self.permissions = permission_engine or (orchestrator.permissions if orchestrator else PermissionEngine())
        self.events = event_bus or (orchestrator.events if orchestrator else None)
        self.notifications = notification_center or (orchestrator.notifications if orchestrator else None)
        self.orchestrator = orchestrator

        # Step dispatcher: delegate to orchestrator if available
        dispatcher = self._create_dispatcher()
        self.runner = AutomationRunner(
            store=self.store,
            permission_engine=self.permissions,
            event_bus=self.events,
            notification_center=self.notifications,
            tool_dispatcher=dispatcher,
        )

        self.worker = AutomationWorker(store=self.store, runner=self.runner)

        # Wire EventBus listener for event-based triggers
        if self.events:
            self.events.subscribe(self._handle_system_event)

        # Seed default templates if database is empty
        self._seed_templates_if_empty()

    def _create_dispatcher(self) -> Callable[[str, Dict[str, Any]], Any]:
        async def dispatch(tool_name: str, args: Dict[str, Any]) -> Any:
            if self.orchestrator and hasattr(self.orchestrator, "tools"):
                tool = self.orchestrator.tools.get_tool(tool_name)
                if tool:
                    return await tool.run(**args)
            return {"tool": tool_name, "status": "executed", "arguments": args}
        return dispatch

    def _seed_templates_if_empty(self) -> None:
        existing = self.store.list_automations()
        if not existing:
            for tpl in get_default_templates():
                # Templates start enabled or ready for user activation
                if tpl.trigger.schedule and not tpl.next_run:
                    nxt = TimeTriggerEvaluator.calculate_next_run(tpl.trigger.schedule)
                    if nxt:
                        tpl.next_run = nxt.isoformat()
                self.store.save_automation(tpl)

    def start(self) -> None:
        """Starts background worker."""
        self.worker.start()

    def stop(self) -> None:
        """Stops background worker."""
        self.worker.stop()

    # ==========================================================================
    # Event Bus Subscription Handler
    # ==========================================================================

    def _handle_system_event(self, event: Event) -> None:
        """Invoked when the system event bus emits an event (e.g. TASK_COMPLETED, device connected)."""
        asyncio.create_task(self._process_event(event))

    async def _process_event(self, event: Event) -> None:
        event_name = event.event_type.value if hasattr(event.event_type, "value") else str(event.event_type)
        active_automations = self.store.list_automations(status=AutomationStatus.ACTIVE)

        for auto in active_automations:
            if not auto.enabled:
                continue

            matches = False
            if auto.trigger.type == TriggerType.EVENT:
                matches = EventTriggerMatcher.matches_event(auto.trigger, event_name, event.data)
            elif auto.trigger.type == TriggerType.DEVICE and "device" in event_name.lower():
                dev_id = event.data.get("device_id", "*")
                matches = EventTriggerMatcher.matches_device_event(auto.trigger, dev_id)

            if matches:
                logger.info(f"Event '{event_name}' matched trigger for automation '{auto.name}' ({auto.id})")
                ctx = {"trigger": "event", "event_type": event_name, "data": event.data, "timestamp": event.timestamp}
                asyncio.create_task(self.runner.run_automation(auto, trigger_context=ctx))

    # ==========================================================================
    # High-Level Automation Operations
    # ==========================================================================

    def create_automation(self, automation: Automation) -> Automation:
        if automation.trigger.schedule and not automation.next_run:
            nxt = TimeTriggerEvaluator.calculate_next_run(automation.trigger.schedule)
            if nxt:
                automation.next_run = nxt.isoformat()
        return self.store.save_automation(automation)

    def create_from_prompt(self, prompt: str, owner: str = "user") -> Automation:
        auto = AutomationDSL.compile_prompt_to_automation(prompt, owner=owner)
        return self.create_automation(auto)

    def edit_from_prompt(self, automation_id: str, prompt: str) -> Optional[Automation]:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return None
        updated = AutomationDSL.edit_automation_with_prompt(auto, prompt)
        return self.create_automation(updated)

    def get_automation(self, automation_id: str) -> Optional[Automation]:
        return self.store.get_automation(automation_id)

    def list_automations(self, status: Optional[AutomationStatus] = None) -> List[Automation]:
        return self.store.list_automations(status=status)

    def delete_automation(self, automation_id: str) -> bool:
        return self.store.delete_automation(automation_id)

    def enable_automation(self, automation_id: str) -> bool:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return False
        auto.enabled = True
        auto.status = AutomationStatus.ACTIVE
        if auto.trigger.schedule:
            nxt = TimeTriggerEvaluator.calculate_next_run(auto.trigger.schedule)
            auto.next_run = nxt.isoformat() if nxt else None
        self.store.save_automation(auto)
        return True

    def disable_automation(self, automation_id: str) -> bool:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return False
        auto.enabled = False
        auto.status = AutomationStatus.DISABLED
        self.store.save_automation(auto)
        return True

    def pause_automation(self, automation_id: str) -> bool:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return False
        auto.enabled = False
        auto.status = AutomationStatus.PAUSED
        self.store.save_automation(auto)
        return True

    def resume_automation(self, automation_id: str) -> bool:
        return self.enable_automation(automation_id)

    async def run_automation_now(
        self,
        automation_id: str,
        trigger_context: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ) -> Optional[AutomationRun]:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return None
        return await self.runner.run_automation(auto, trigger_context=trigger_context, dry_run=dry_run)

    def get_history(self, automation_id: Optional[str] = None, limit: int = 50) -> List[AutomationRun]:
        return self.store.list_runs(automation_id=automation_id, limit=limit)

    def get_run(self, run_id: str) -> Optional[AutomationRun]:
        return self.store.get_run(run_id)

    def get_templates(self) -> List[Automation]:
        return get_default_templates()

    def preview_automation(self, automation_or_dict: Union[Automation, Dict[str, Any]]) -> Dict[str, Any]:
        if isinstance(automation_or_dict, dict):
            ok, errs, auto = AutomationDSL.validate_automation(automation_or_dict)
            if not ok or not auto:
                return {"valid": False, "errors": errs}
            preview = AutomationDSL.generate_preview(auto)
            preview["valid"] = True
            return preview
        return AutomationDSL.generate_preview(automation_or_dict)

    def dry_run(self, automation_id: str, simulated_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        auto = self.store.get_automation(automation_id)
        if not auto:
            return {"success": False, "error": f"Automation {automation_id} not found"}
        return AutomationDSL.dry_run_simulation(auto, simulated_context or {})

    def get_analytics(self) -> Dict[str, Any]:
        """Calculates global automation health and execution metrics."""
        automations = self.store.list_automations()
        runs = self.store.list_runs(limit=200)

        total_runs = len(runs)
        successes = sum(1 for r in runs if r.status == RunStatus.COMPLETED)
        failures = sum(1 for r in runs if r.status == RunStatus.FAILED)
        skipped = sum(1 for r in runs if r.status == RunStatus.SKIPPED)

        success_rate = round((successes / total_runs * 100), 1) if total_runs > 0 else 100.0

        return {
            "total_automations": len(automations),
            "active": sum(1 for a in automations if a.status == AutomationStatus.ACTIVE and a.enabled),
            "paused": sum(1 for a in automations if a.status == AutomationStatus.PAUSED or not a.enabled),
            "needs_attention": sum(1 for a in automations if a.failure_count > 2),
            "total_runs": total_runs,
            "success_rate": success_rate,
            "successful_runs": successes,
            "failed_runs": failures,
            "skipped_runs": skipped,
        }
