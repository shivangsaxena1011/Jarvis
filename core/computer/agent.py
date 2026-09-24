"""
SHIVANI Master Computer Autonomy Agent (Phase 17).
Provides closed-loop desktop operation:
OBSERVE -> UNDERSTAND -> PLAN -> ACT -> OBSERVE -> VERIFY -> RECOVER -> REPORT.
"""

from __future__ import annotations
import asyncio
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from core.computer.adapters import AdapterRegistry, create_default_adapter_registry
from core.computer.checkpoint_engine import CheckpointEngine
from core.computer.execution_engine import ExecutionEngine
from core.computer.expectation_engine import ExpectationEngine
from core.computer.models import (
    ActionExecutionResult,
    ActionType,
    ApplicationContext,
    ApplicationState,
    ComputerAction,
    DesktopObservation,
    ErrorType,
    StateDifference,
    TaskCheckpoint,
    UIElement,
)
from core.computer.observation_engine import ObservationEngine
from core.computer.recovery_engine import ComputerRecoveryEngine
from core.computer.resource_lock import ActionPriority, ResourceLockManager
from core.computer.semantic_graph import UISemanticGraph
from core.computer.terminal_controller import TerminalController
from core.computer.uia_engine import UIAEngine
from core.computer.visual_grounding import MultiSourceGrounder
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter

logger = logging.getLogger("shivani.computer.agent")


class ComputerAutonomyAgent:
    """
    Genuine closed-loop, confidence-aware computer-use agent
    capable of operating open-ended desktop environments.
    """

    def __init__(
        self,
        os_adapter: Optional[OperatingSystemAdapter] = None,
        checkpoints_dir: Optional[str] = None,
    ):
        self.os_adapter = os_adapter or get_os_adapter()
        self.lock_manager = ResourceLockManager()
        self.uia_engine = UIAEngine()
        self.observation_engine = ObservationEngine(self.os_adapter, self.uia_engine)
        self.execution_engine = ExecutionEngine(
            os_adapter=self.os_adapter,
            observation_engine=self.observation_engine,
            lock_manager=self.lock_manager,
            uia_engine=self.uia_engine,
        )
        self.grounder = MultiSourceGrounder()
        self.expectation_engine = ExpectationEngine()
        self.recovery_engine = ComputerRecoveryEngine()
        self.checkpoint_engine = CheckpointEngine(checkpoints_dir=checkpoints_dir)
        self.terminal = TerminalController()
        self.adapter_registry = create_default_adapter_registry()

        self._current_observation: Optional[DesktopObservation] = None
        self._current_semantic_graph: Optional[UISemanticGraph] = None

    async def observe(
        self,
        capture_image: bool = True,
        synthetic_override: Optional[DesktopObservation] = None,
    ) -> DesktopObservation:
        """Captures world state and updates the semantic UI graph."""
        obs = await self.observation_engine.observe(
            capture_image=capture_image, synthetic_override=synthetic_override
        )
        self._current_observation = obs
        self._current_semantic_graph = UISemanticGraph(obs.elements)
        return obs

    async def execute_action(
        self,
        action: ComputerAction,
        synthetic_post_obs: Optional[DesktopObservation] = None,
    ) -> ActionExecutionResult:
        """
        Executes a single action through the verified closed loop.
        """
        # Ensure we have a fresh pre-observation
        pre_obs = self._current_observation or await self.observe(capture_image=False)

        res = await self.execution_engine.execute_closed_loop(
            action=action,
            pre_observation=pre_obs,
            synthetic_post_obs=synthetic_post_obs,
        )

        if res.observation_after:
            self._current_observation = res.observation_after
            self._current_semantic_graph = UISemanticGraph(res.observation_after.elements)

        # Loop detection recording
        if self._current_observation:
            loop_detected = self.recovery_engine.loop_detector.record_step(
                action, self._current_observation
            )
            if loop_detected:
                res.verified = False
                res.success = False
                res.error_type = ErrorType.LOOP_DETECTED
                res.failure_reason = "Automation loop detected: identical action or oscillating state."

        return res

    async def execute_task_workflow(
        self,
        task_id: str,
        steps: List[Dict[str, Any]],
        max_actions: int = 25,
        max_runtime_seconds: float = 300.0,
    ) -> Dict[str, Any]:
        """
        Executes a multi-step long-horizon computer workflow with checkpointing,
        progress verification, loop detection, and dynamic recovery.
        """
        start_time = time.time()
        completed_actions: List[Dict[str, Any]] = []
        action_count = 0
        step_index = 0

        # Initial observation
        current_obs = await self.observe(capture_image=False)

        # Acquire desktop lock
        locked = self.lock_manager.acquire_lock(
            resource="Desktop",
            holder_id=task_id,
            priority=ActionPriority.USER_APPROVED_TASK,
            reason=f"Workflow {task_id}",
        )
        if not locked:
            return {
                "success": False,
                "task_id": task_id,
                "error": "Failed to acquire Desktop lock. Higher priority task or manual takeover active.",
            }

        try:
            while step_index < len(steps):
                # Budget check
                if action_count >= max_actions:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "error": f"Resource budget exceeded: max {max_actions} actions reached.",
                        "completed_actions": completed_actions,
                    }

                if time.time() - start_time > max_runtime_seconds:
                    return {
                        "success": False,
                        "task_id": task_id,
                        "error": f"Runtime budget exceeded: {max_runtime_seconds}s limit reached.",
                        "completed_actions": completed_actions,
                    }

                # Check user interrupt
                if self.lock_manager.is_emergency_stopped:
                    self.checkpoint_engine.create_checkpoint(
                        task_id=task_id,
                        step_index=step_index,
                        app_context=current_obs.application_context,
                        completed_actions=completed_actions,
                        pending_steps=[s.get("description", str(s)) for s in steps[step_index:]],
                        summary="Emergency stop invoked during workflow",
                    )
                    return {
                        "success": False,
                        "task_id": task_id,
                        "interrupted": True,
                        "message": "Task halted by emergency stop.",
                    }

                raw_step = steps[step_index]
                action = self._build_action_from_step(raw_step)

                # Checkpoint before critical action
                self.checkpoint_engine.create_checkpoint(
                    task_id=task_id,
                    step_index=step_index,
                    app_context=current_obs.application_context,
                    completed_actions=completed_actions,
                    pending_steps=[s.get("description", str(s)) for s in steps[step_index:]],
                )

                # Execute action closed loop
                result = await self.execute_action(action)
                action_count += 1
                completed_actions.append(result.model_dump())

                if not result.verified:
                    # Attempt recovery
                    strategy = self.recovery_engine.select_recovery_strategy(
                        error_type=result.error_type or ErrorType.APPLICATION_ERROR,
                        failed_action=action,
                        retry_count=1,
                    )

                    if strategy["strategy"] == "PAUSE_FOR_HUMAN":
                        return {
                            "success": False,
                            "task_id": task_id,
                            "paused": True,
                            "reason": strategy["reason"],
                            "completed_actions": completed_actions,
                        }

                    if strategy["strategy"] == "ABORT_AND_PAUSE":
                        return {
                            "success": False,
                            "task_id": task_id,
                            "error": strategy["reason"],
                            "completed_actions": completed_actions,
                        }

                step_index += 1
                current_obs = self._current_observation or await self.observe(capture_image=False)

            return {
                "success": True,
                "task_id": task_id,
                "completed_actions": len(completed_actions),
                "duration_seconds": time.time() - start_time,
                "verified": True,
            }

        finally:
            self.lock_manager.release_lock("Desktop", task_id)

    def _build_action_from_step(self, step: Dict[str, Any]) -> ComputerAction:
        atype_str = step.get("type", "click").lower()
        try:
            atype = ActionType(atype_str)
        except ValueError:
            atype = ActionType.CLICK

        return ComputerAction(
            action_type=atype,
            target=step.get("target"),
            parameters=step.get("parameters", {}),
            expected_state=step.get("expected_state", {}),
            risk=step.get("risk", "LOW"),
            confidence=step.get("confidence", 1.0),
        )

    def emergency_stop(self):
        """Immediately interrupts all activity and locks down operations."""
        self.lock_manager.emergency_stop()

    def manual_takeover(self):
        """Surrenders control to human user."""
        self.lock_manager.begin_manual_takeover()

    def resume_from_takeover(self):
        """Releases takeover and forces complete re-observation."""
        self.lock_manager.end_manual_takeover()
        self._current_observation = None
        self._current_semantic_graph = None
