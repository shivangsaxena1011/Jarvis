"""
SHIVANI Background Automation Worker (Phase 15).
Runs in the background, evaluates schedules, reconciles missed jobs after sleep/wake,
respects battery/resource constraints, and dispatches due workflows safely.
"""

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Dict, List, Optional

from core.automation.models import Automation, AutomationStatus, TriggerType
from core.automation.runner import AutomationRunner
from core.automation.store import AutomationStore
from core.automation.triggers import TimeTriggerEvaluator

logger = logging.getLogger("shivani.automation.worker")


class AutomationWorker:
    """Autonomous background scheduler and reconciliation worker."""

    def __init__(
        self,
        store: AutomationStore,
        runner: AutomationRunner,
        tick_interval_seconds: float = 2.0,
        battery_check_fn: Optional[callable] = None,
    ):
        self.store = store
        self.runner = runner
        self.tick_interval_seconds = tick_interval_seconds
        self.battery_check_fn = battery_check_fn
        self._is_running = False
        self._worker_task: Optional[asyncio.Task] = None
        self._last_tick_time = time.time()
        self._user_interrupted = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self._last_tick_time = time.time()
        self._worker_task = asyncio.create_task(self._run_loop())
        logger.info("AutomationWorker started.")

    def stop(self) -> None:
        self._is_running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
        logger.info("AutomationWorker stopped.")

    def set_user_busy(self, busy: bool) -> None:
        """Pause or yield background automation processing when user is interacting."""
        self._user_interrupted = busy

    async def _run_loop(self) -> None:
        while self._is_running:
            try:
                now_epoch = time.time()
                elapsed_since_last_tick = now_epoch - self._last_tick_time
                self._last_tick_time = now_epoch

                # Detect sleep/wake or hibernation jump (gap > 30s beyond normal tick)
                if elapsed_since_last_tick > (self.tick_interval_seconds + 30.0):
                    logger.warning(
                        f"System sleep/wake event detected! (Tick gap: {elapsed_since_last_tick:.1f}s). Reconciling missed jobs."
                    )
                    await self._reconcile_sleep_wake()

                # Process normal due jobs
                await self.tick()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in AutomationWorker loop: {e}", exc_info=True)

            await asyncio.sleep(self.tick_interval_seconds)

    async def tick(self) -> List[str]:
        """Single tick evaluation across all active automations."""
        if self._user_interrupted:
            # Yield priority to interactive user
            return []

        # Battery / Resource Check
        if self.battery_check_fn:
            try:
                battery_pct = self.battery_check_fn()
                if battery_pct is not None and battery_pct < 20:
                    logger.warning(f"Battery low ({battery_pct}%). Deferring background automations.")
                    return []
            except Exception:
                pass

        now = datetime.now(timezone.utc)
        active_automations = self.store.list_automations(status=AutomationStatus.ACTIVE)
        dispatched_ids: List[str] = []

        for auto in active_automations:
            if not auto.enabled:
                continue

            # Ensure next_run is calculated if missing
            if not auto.next_run and auto.trigger.schedule:
                nxt = TimeTriggerEvaluator.calculate_next_run(auto.trigger.schedule, from_time=now)
                if nxt:
                    auto.next_run = nxt.isoformat()
                    self.store.save_automation(auto)

            is_due, _ = TimeTriggerEvaluator.is_due(auto, now)
            if is_due:
                logger.info(f"Triggering scheduled automation: {auto.name} ({auto.id})")
                dispatched_ids.append(auto.id)

                # Schedule next run before or after execution
                if auto.trigger.type == TriggerType.ONCE:
                    auto.enabled = False
                    auto.status = AutomationStatus.DISABLED
                elif auto.trigger.schedule:
                    nxt = TimeTriggerEvaluator.calculate_next_run(auto.trigger.schedule, from_time=now)
                    auto.next_run = nxt.isoformat() if nxt else None

                self.store.save_automation(auto)

                # Fire execution asynchronously
                asyncio.create_task(self.runner.run_automation(auto, trigger_context={"trigger": "schedule", "time": now.isoformat()}))

        return dispatched_ids

    async def _reconcile_sleep_wake(self) -> None:
        """Reconciles missed jobs after system hibernation or wake."""
        now = datetime.now(timezone.utc)
        automations = self.store.list_automations(status=AutomationStatus.ACTIVE)

        for auto in automations:
            if not auto.enabled or not auto.next_run:
                continue

            is_due, _ = TimeTriggerEvaluator.is_due(auto, now)
            if is_due:
                policy = auto.trigger.schedule.catch_up_policy if auto.trigger.schedule else "run_latest"

                if policy == "skip_if_missed":
                    logger.info(f"Skipping missed automation {auto.name} per 'skip_if_missed' policy.")
                    if auto.trigger.schedule:
                        nxt = TimeTriggerEvaluator.calculate_next_run(auto.trigger.schedule, from_time=now)
                        auto.next_run = nxt.isoformat() if nxt else None
                        self.store.save_automation(auto)

                elif policy == "run_latest":
                    logger.info(f"Catching up missed automation {auto.name} (running once).")
                    if auto.trigger.schedule:
                        nxt = TimeTriggerEvaluator.calculate_next_run(auto.trigger.schedule, from_time=now)
                        auto.next_run = nxt.isoformat() if nxt else None
                        self.store.save_automation(auto)
                    asyncio.create_task(self.runner.run_automation(auto, trigger_context={"trigger": "sleep_wake_catchup", "time": now.isoformat()}))
