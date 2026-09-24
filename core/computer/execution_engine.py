"""
SHIVANI Closed-Loop Computer Action Execution Engine (Phase 17).
Executes actions through the closed-loop cycle:
OBSERVE -> TARGET VALIDATE -> ACT -> OBSERVE -> VERIFY.
"""

from __future__ import annotations
import asyncio
import time
from typing import Any, Dict, List, Optional, Tuple

from core.computer.expectation_engine import ExpectationEngine
from core.computer.models import (
    ActionExecutionResult,
    ActionType,
    ComputerAction,
    DesktopObservation,
    ErrorType,
    StateDifference,
)
from core.computer.observation_engine import ObservationEngine
from core.computer.resource_lock import ActionPriority, ResourceLockManager
from core.computer.uia_engine import UIAEngine
from core.computer.visual_grounding import MultiSourceGrounder
from tools.desktop.os.base import OperatingSystemAdapter
from tools.desktop.os.factory import get_os_adapter


class ExecutionEngine:
    """Manages closed-loop action dispatch, input synthesis, and outcome verification."""

    def __init__(
        self,
        os_adapter: Optional[OperatingSystemAdapter] = None,
        observation_engine: Optional[ObservationEngine] = None,
        lock_manager: Optional[ResourceLockManager] = None,
        uia_engine: Optional[UIAEngine] = None,
    ):
        self.os_adapter = os_adapter or get_os_adapter()
        self.observation_engine = observation_engine or ObservationEngine(self.os_adapter)
        self.lock_manager = lock_manager or ResourceLockManager()
        self.uia_engine = uia_engine or UIAEngine()
        self.grounder = MultiSourceGrounder()
        self.expectation_engine = ExpectationEngine()

    async def execute_closed_loop(
        self,
        action: ComputerAction,
        pre_observation: Optional[DesktopObservation] = None,
        synthetic_post_obs: Optional[DesktopObservation] = None,
    ) -> ActionExecutionResult:
        """
        Executes a single computer action in a strict closed-loop cycle.
        """
        start_time = time.time()

        # Check emergency stop or manual takeover
        if self.lock_manager.is_emergency_stopped:
            return ActionExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                success=False,
                verified=False,
                failure_reason="Emergency stop is active. Aborting action.",
                error_type=ErrorType.PERMISSION_DENIED,
            )

        if self.lock_manager.is_manual_takeover:
            return ActionExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                success=False,
                verified=False,
                failure_reason="User manual takeover is active. Automated action deferred.",
                error_type=ErrorType.INVALID_STATE,
            )

        # 1. PRE-OBSERVE
        obs_before = pre_observation or await self.observation_engine.observe(capture_image=False)

        # 2. RESOLVE TARGET / COORDINATES (if action targets a named element)
        target_coords: Optional[Tuple[int, int]] = None
        if action.target and action.action_type in (ActionType.CLICK, ActionType.DOUBLE_CLICK, ActionType.RIGHT_CLICK):
            grounding = self.grounder.ground(action.target, obs_before.elements)
            if grounding.ambiguous or grounding.element is None:
                # Target unresolved or ambiguous
                if not action.parameters.get("x") or not action.parameters.get("y"):
                    return ActionExecutionResult(
                        action_id=action.id,
                        action_type=action.action_type,
                        success=False,
                        verified=False,
                        failure_reason=f"Target '{action.target}' is ambiguous or not found (confidence: {grounding.confidence:.2f}).",
                        error_type=ErrorType.ELEMENT_NOT_FOUND,
                    )
            else:
                target_coords = grounding.target_point

        # 3. ACT (Dispatch input)
        dispatch_success = await self._dispatch_action(action, target_coords)
        if not dispatch_success:
            return ActionExecutionResult(
                action_id=action.id,
                action_type=action.action_type,
                success=False,
                verified=False,
                failure_reason="Failed to dispatch input action to OS.",
                error_type=ErrorType.APPLICATION_ERROR,
            )

        # Brief pause to allow OS event queue and UI animation to settle
        await asyncio.sleep(0.1)

        # 4. POST-OBSERVE
        obs_after = (
            synthetic_post_obs
            if synthetic_post_obs is not None
            else await self.observation_engine.observe(capture_image=False)
        )

        # 5. VERIFY
        diff = self.expectation_engine.compute_state_difference(obs_before, obs_after)
        verified, failures = self.expectation_engine.verify_action_outcome(
            action, obs_before, obs_after, diff
        )

        duration = time.time() - start_time
        failure_msg = "; ".join(failures) if not verified else None
        err_type = ErrorType.INVALID_STATE if not verified else None

        return ActionExecutionResult(
            action_id=action.id,
            action_type=action.action_type,
            success=verified,
            verified=verified,
            state_diff=diff,
            duration_seconds=duration,
            confidence=action.confidence,
            failure_reason=failure_msg,
            error_type=err_type,
            observation_after=obs_after,
        )

    async def _dispatch_action(
        self, action: ComputerAction, target_coords: Optional[Tuple[int, int]]
    ) -> bool:
        """Dispatches physical/virtual input via OperatingSystemAdapter or UIA."""
        t = action.action_type
        p = action.parameters

        try:
            if t == ActionType.CLICK:
                x = p.get("x", target_coords[0] if target_coords else 0)
                y = p.get("y", target_coords[1] if target_coords else 0)
                button = p.get("button", "left")
                await self.os_adapter.mouse_click(button=button, x=x, y=y, clicks=1)
                return True

            elif t == ActionType.DOUBLE_CLICK:
                x = p.get("x", target_coords[0] if target_coords else 0)
                y = p.get("y", target_coords[1] if target_coords else 0)
                await self.os_adapter.mouse_click(button="left", x=x, y=y, clicks=2)
                return True

            elif t == ActionType.RIGHT_CLICK:
                x = p.get("x", target_coords[0] if target_coords else 0)
                y = p.get("y", target_coords[1] if target_coords else 0)
                await self.os_adapter.mouse_click(button="right", x=x, y=y, clicks=1)
                return True

            elif t == ActionType.TYPE:
                text = p.get("text", "")
                await self.os_adapter.type_text(text)
                return True

            elif t == ActionType.KEY_PRESS:
                key = p.get("key", "")
                await self.os_adapter.key_press(key)
                return True

            elif t == ActionType.HOTKEY:
                keys = p.get("keys", [])
                await self.os_adapter.hotkey(*keys)
                return True

            elif t == ActionType.SCROLL:
                clicks = p.get("clicks", -3)
                await self.os_adapter.mouse_scroll(clicks)
                return True

            elif t == ActionType.DRAG:
                start_x = p.get("start_x", 0)
                start_y = p.get("start_y", 0)
                end_x = p.get("end_x", 0)
                end_y = p.get("end_y", 0)
                await self.os_adapter.mouse_drag(start_x, start_y, end_x, end_y)
                return True

            elif t == ActionType.OPEN:
                app_name = p.get("app_name") or action.target or ""
                args = p.get("args")
                res = await self.os_adapter.launch_app(app_name, args=args)
                return res.get("status") == "LAUNCHED"

            elif t == ActionType.CLOSE:
                target = action.target or p.get("window_id")
                return await self.os_adapter.close_window(target)

            elif t == ActionType.MAXIMIZE:
                target = action.target or p.get("window_id")
                return await self.os_adapter.maximize_window(target)

            elif t == ActionType.MINIMIZE:
                target = action.target or p.get("window_id")
                return await self.os_adapter.minimize_window(target)

            return True
        except Exception:
            return False
