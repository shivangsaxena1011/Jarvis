"""
SHIVANI Computer Recovery, Adaptive Retry & Loop Detection Engine (Phase 17).
Monitors action history, detects automation loops, classifies errors,
and dynamically replans execution strategies.
"""

from __future__ import annotations
from collections import deque
import hashlib
import time
from typing import Any, Deque, Dict, List, Optional, Tuple
from core.computer.models import (
    ActionType,
    ComputerAction,
    DesktopObservation,
    ErrorType,
)


class LoopDetector:
    """Detects repetitive actions or oscillating states in computer operations."""

    def __init__(self, history_size: int = 10, max_repeats: int = 3):
        self.max_repeats = max_repeats
        self.action_history: Deque[str] = deque(maxlen=history_size)
        self.state_history: Deque[str] = deque(maxlen=history_size)

    def record_step(self, action: ComputerAction, observation: DesktopObservation) -> bool:
        """
        Records a step and returns True if an automation loop is detected.
        """
        # Create action fingerprint
        action_sig = f"{action.action_type.value}:{action.target}:{action.parameters.get('key', '')}:{action.parameters.get('text', '')}"
        self.action_history.append(action_sig)

        # Create state fingerprint (window + elements count + top elements text)
        elem_texts = ",".join(e.text for e in observation.elements[:5])
        state_sig = f"{observation.active_window}:{len(observation.elements)}:{elem_texts}"
        self.state_history.append(state_sig)

        return self.is_loop_detected()

    def is_loop_detected(self) -> bool:
        if len(self.action_history) < self.max_repeats:
            return False

        # 1. Exact identical action repetition
        recent_actions = list(self.action_history)[-self.max_repeats:]
        if len(set(recent_actions)) == 1:
            return True

        # 2. Oscillating states (A -> B -> A -> B)
        if len(self.state_history) >= 4:
            s = list(self.state_history)
            if s[-1] == s[-3] and s[-2] == s[-4] and s[-1] != s[-2]:
                return True

        return False


class ComputerRecoveryEngine:
    """Manages adaptive error recovery strategies and dynamic replanning."""

    def __init__(self):
        self.loop_detector = LoopDetector()

    def classify_error(self, message: str, context: Optional[Dict[str, Any]] = None) -> ErrorType:
        msg = message.lower()
        if "not found" in msg or "could not find" in msg or "element" in msg:
            return ErrorType.ELEMENT_NOT_FOUND
        if "ui changed" in msg or "disappeared" in msg:
            return ErrorType.UI_CHANGED
        if "timed out" in msg or "timeout" in msg:
            return ErrorType.TIMEOUT
        if "permission" in msg or "access denied" in msg or "elevated" in msg:
            return ErrorType.PERMISSION_DENIED
        if "auth" in msg or "login" in msg or "password" in msg:
            return ErrorType.AUTH_REQUIRED
        if "crash" in msg or "not responding" in msg or "died" in msg:
            return ErrorType.CRASH
        if "loop" in msg or "oscillation" in msg:
            return ErrorType.LOOP_DETECTED
        if "network" in msg or "connection" in msg:
            return ErrorType.NETWORK_ERROR
        return ErrorType.APPLICATION_ERROR

    def select_recovery_strategy(
        self,
        error_type: ErrorType,
        failed_action: ComputerAction,
        retry_count: int,
    ) -> Dict[str, Any]:
        """
        Determines the next recovery strategy based on error classification.
        """
        if error_type == ErrorType.LOOP_DETECTED:
            return {
                "strategy": "ABORT_AND_PAUSE",
                "reason": "Automation loop detected. Pausing for safety.",
                "replan": False,
            }

        if error_type == ErrorType.AUTH_REQUIRED:
            return {
                "strategy": "PAUSE_FOR_HUMAN",
                "reason": "Authentication or security challenge detected. Waiting for manual login.",
                "replan": False,
            }

        if error_type == ErrorType.ELEMENT_NOT_FOUND:
            if retry_count == 1:
                # First retry: Re-observe and search via OCR/Vision
                return {
                    "strategy": "REOBSERVE_AND_SEARCH_OCR",
                    "action_override": None,
                    "replan": False,
                }
            elif retry_count == 2:
                # Second retry: Try keyboard shortcut alternative if available
                return {
                    "strategy": "KEYBOARD_SHORTCUT_FALLBACK",
                    "replan": True,
                }
            else:
                return {
                    "strategy": "ASK_USER_CLARIFICATION",
                    "replan": False,
                }

        if error_type == ErrorType.UI_CHANGED:
            return {
                "strategy": "REOBSERVE_AND_REPLAN",
                "replan": True,
            }

        if error_type == ErrorType.CRASH:
            return {
                "strategy": "RESTART_APPLICATION_AND_RESUME",
                "replan": True,
            }

        # Default backoff
        return {
            "strategy": "BACKOFF_RETRY",
            "backoff_seconds": 1.0 * (2 ** retry_count),
            "replan": False,
        }

    def dynamic_replan(
        self,
        current_plan_steps: List[str],
        current_step_index: int,
        observation: DesktopObservation,
    ) -> List[str]:
        """
        Adjusts remaining plan steps based on current observed reality.
        """
        replanned = list(current_plan_steps)
        if current_step_index >= len(replanned):
            return replanned

        current_step = replanned[current_step_index]

        # Check if current step's goal is already satisfied in the UI:
        # e.g. "Open VS Code" when VS Code is already active
        if "open vs code" in current_step.lower() and "visual studio code" in observation.active_window.lower():
            # Step already satisfied, skip it
            replanned.pop(current_step_index)
        elif "open terminal" in current_step.lower() and "terminal" in observation.active_window.lower():
            replanned.pop(current_step_index)

        return replanned
