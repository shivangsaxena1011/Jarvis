"""
SHIVANI Expectation Engine & State Difference Detector (Phase 17).
Defines action expectations and verifies state changes between pre-action
and post-action desktop observations.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from core.computer.models import (
    ActionType,
    ComputerAction,
    DesktopObservation,
    ElementType,
    StateDifference,
)


class ExpectationEngine:
    """Computes expected post-conditions and verifies state transitions."""

    @staticmethod
    def infer_expectation(action: ComputerAction) -> Dict[str, Any]:
        """
        Infers standard expected state changes if not explicitly provided.
        """
        exp: Dict[str, Any] = dict(action.expected_state)
        t = action.action_type

        if t == ActionType.OPEN:
            app_target = action.parameters.get("app_name") or action.target or ""
            exp.setdefault("app_launched", app_target)
            exp.setdefault("window_should_be_active", True)
        elif t == ActionType.CLOSE:
            exp.setdefault("window_closed", True)
        elif t == ActionType.CLICK:
            exp.setdefault("state_should_change", True)
        elif t == ActionType.TYPE:
            typed_text = action.parameters.get("text", "")
            if typed_text:
                exp.setdefault("text_should_appear", typed_text)
        elif t == ActionType.MAXIMIZE:
            exp.setdefault("window_maximized", True)
        elif t == ActionType.MINIMIZE:
            exp.setdefault("window_minimized", True)

        return exp

    @staticmethod
    def compute_state_difference(
        before: DesktopObservation,
        after: DesktopObservation,
    ) -> StateDifference:
        """
        Computes the structural delta between pre-action and post-action world states.
        """
        diff = StateDifference()

        # 1. Active window changes
        if before.active_window != after.active_window:
            diff.active_window_changed = True
            diff.new_window_title = after.active_window

        # 2. Dialog detection
        before_dialogs = [e for e in before.elements if e.type == ElementType.DIALOG]
        after_dialogs = [e for e in after.elements if e.type == ElementType.DIALOG]
        if len(after_dialogs) > len(before_dialogs):
            diff.new_dialog_detected = True
            diff.dialog_type = after_dialogs[-1].text or "Modal Dialog"

        # 3. Text delta (from OCR or UI texts)
        before_texts = set(e.text.strip().lower() for e in before.elements if e.text)
        after_texts = set(e.text.strip().lower() for e in after.elements if e.text)

        added = list(after_texts - before_texts)
        removed = list(before_texts - after_texts)

        if added or removed:
            diff.text_changed = True
            diff.added_text = added[:10]
            diff.removed_text = removed[:10]

        # 4. Element count delta
        diff.elements_added = max(0, len(after.elements) - len(before.elements))
        diff.elements_removed = max(0, len(before.elements) - len(after.elements))

        # 5. Error detection
        for elem in after.elements:
            txt_lower = elem.text.lower()
            if any(err in txt_lower for err in ["error", "fatal", "failed to open", "not responding", "exception"]):
                diff.error_detected = True
                diff.error_message = elem.text
                break

        return diff

    @staticmethod
    def verify_action_outcome(
        action: ComputerAction,
        before: DesktopObservation,
        after: DesktopObservation,
        diff: StateDifference,
    ) -> Tuple[bool, List[str]]:
        """
        Verifies whether the actual state difference satisfies the action's expectations.
        Returns (verified: bool, failures: List[str]).
        """
        exp = action.expected_state
        if not exp:
            # If no expectations explicitly declared, check for negative states (e.g. unexpected errors or crash)
            if diff.error_detected and not action.parameters.get("expect_error"):
                return False, [f"Unexpected error appeared: '{diff.error_message}'"]
            return True, []

        failures: List[str] = []

        # Check: expected window title
        if "window_title" in exp:
            expected_win = exp["window_title"].lower()
            if expected_win not in after.active_window.lower():
                failures.append(f"Expected active window containing '{exp['window_title']}', but active is '{after.active_window}'")

        # Check: expected text to appear
        if "text_should_appear" in exp:
            req_text = exp["text_should_appear"].lower()
            found = any(req_text in e.text.lower() for e in after.elements)
            if not found:
                failures.append(f"Expected text '{exp['text_should_appear']}' to appear in observation, but not found")

        # Check: expected dialog
        if exp.get("expect_dialog"):
            if not diff.new_dialog_detected:
                failures.append("Expected a new dialog to open, but none was detected")

        # Check: expected error
        if not exp.get("expect_error") and diff.error_detected:
            failures.append(f"Application error appeared: '{diff.error_message}'")

        return len(failures) == 0, failures
