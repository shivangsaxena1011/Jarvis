"""
SHIVANI Condition Engine (Phase 15).
Safe structured predicate evaluation (equals, contains, greater_than, etc.)
with composite boolean logic (AND, OR, NOT). Zero arbitrary code execution.
"""

import re
from typing import Any, Dict, Optional

from core.automation.models import (
    ConditionGroup,
    ConditionOperator,
    ConditionPredicate,
    LogicalOperator,
)


class ConditionEngine:
    """Evaluates structured condition trees against runtime context without eval/exec."""

    @classmethod
    def evaluate_group(cls, group: Optional[ConditionGroup], context: Dict[str, Any]) -> bool:
        if not group:
            return True

        # Evaluate direct predicates
        pred_results = [cls.evaluate_predicate(p, context) for p in group.predicates]

        # Recursively evaluate nested groups
        nested_results = [cls.evaluate_group(g, context) for g in group.nested_groups]

        all_results = pred_results + nested_results
        if not all_results:
            return True

        if group.logical_op == LogicalOperator.AND:
            return all(all_results)
        elif group.logical_op == LogicalOperator.OR:
            return any(all_results)
        elif group.logical_op == LogicalOperator.NOT:
            # NOT negates the conjunction of all inner results
            return not all(all_results)

        return True

    @classmethod
    def evaluate_predicate(cls, predicate: ConditionPredicate, context: Dict[str, Any]) -> bool:
        actual_value = cls._resolve_path(predicate.field, context)
        expected_value = predicate.value
        op = predicate.operator

        if op == ConditionOperator.EXISTS:
            return actual_value is not None

        if op == ConditionOperator.NOT_EXISTS:
            return actual_value is None

        if actual_value is None:
            return False

        if op == ConditionOperator.EQUALS:
            return actual_value == expected_value

        if op == ConditionOperator.NOT_EQUALS:
            return actual_value != expected_value

        if op == ConditionOperator.CONTAINS:
            if isinstance(actual_value, (list, tuple, set)):
                return expected_value in actual_value
            return str(expected_value).lower() in str(actual_value).lower()

        if op == ConditionOperator.NOT_CONTAINS:
            if isinstance(actual_value, (list, tuple, set)):
                return expected_value not in actual_value
            return str(expected_value).lower() not in str(actual_value).lower()

        if op == ConditionOperator.GREATER_THAN:
            try:
                return float(actual_value) > float(expected_value)
            except (ValueError, TypeError):
                return False

        if op == ConditionOperator.LESS_THAN:
            try:
                return float(actual_value) < float(expected_value)
            except (ValueError, TypeError):
                return False

        if op == ConditionOperator.CHANGED:
            old_val = context.get("__previous_state__", {}).get(predicate.field)
            return old_val != actual_value

        if op == ConditionOperator.MATCHES:
            try:
                return bool(re.search(str(expected_value), str(actual_value)))
            except re.error:
                return False

        return False

    @staticmethod
    def _resolve_path(path: str, context: Dict[str, Any]) -> Any:
        """Safely extracts dot-notated field value from nested dictionary context."""
        parts = path.strip().split(".")
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif hasattr(current, part):
                current = getattr(current, part)
            else:
                return None
            if current is None:
                return None
        return current
