"""
Unit tests for Phase 15 Condition Engine and structured predicate evaluation.
"""

import pytest

from core.automation.conditions import ConditionEngine
from core.automation.models import (
    ConditionGroup,
    ConditionOperator,
    ConditionPredicate,
    LogicalOperator,
)


def test_basic_predicates():
    ctx = {
        "user": {"name": "Shivani", "level": 10},
        "unread_emails": 5,
        "filename": "report.pdf",
    }

    # Equals
    p1 = ConditionPredicate(field="user.name", operator=ConditionOperator.EQUALS, value="Shivani")
    assert ConditionEngine.evaluate_predicate(p1, ctx) is True

    # Not equals
    p2 = ConditionPredicate(field="user.name", operator=ConditionOperator.NOT_EQUALS, value="Bot")
    assert ConditionEngine.evaluate_predicate(p2, ctx) is True

    # Greater than
    p3 = ConditionPredicate(field="unread_emails", operator=ConditionOperator.GREATER_THAN, value=0)
    assert ConditionEngine.evaluate_predicate(p3, ctx) is True

    # Contains
    p4 = ConditionPredicate(field="filename", operator=ConditionOperator.CONTAINS, value=".pdf")
    assert ConditionEngine.evaluate_predicate(p4, ctx) is True

    # Exists
    p5 = ConditionPredicate(field="user.level", operator=ConditionOperator.EXISTS)
    assert ConditionEngine.evaluate_predicate(p5, ctx) is True

    # Matches regex
    p6 = ConditionPredicate(field="filename", operator=ConditionOperator.MATCHES, value=r"\.pdf$")
    assert ConditionEngine.evaluate_predicate(p6, ctx) is True


def test_composite_and_or_not_groups():
    ctx = {
        "event": {"type": "build_failed", "repo": "project-x"},
        "unread_important": 3,
    }

    # Group 1: AND condition
    group_and = ConditionGroup(
        logical_op=LogicalOperator.AND,
        predicates=[
            ConditionPredicate(field="event.type", operator=ConditionOperator.EQUALS, value="build_failed"),
            ConditionPredicate(field="event.repo", operator=ConditionOperator.EQUALS, value="project-x"),
        ],
    )
    assert ConditionEngine.evaluate_group(group_and, ctx) is True

    # Group 2: OR condition
    group_or = ConditionGroup(
        logical_op=LogicalOperator.OR,
        predicates=[
            ConditionPredicate(field="unread_important", operator=ConditionOperator.EQUALS, value=0),
            ConditionPredicate(field="unread_important", operator=ConditionOperator.GREATER_THAN, value=2),
        ],
    )
    assert ConditionEngine.evaluate_group(group_or, ctx) is True

    # Group 3: NOT condition
    group_not = ConditionGroup(
        logical_op=LogicalOperator.NOT,
        predicates=[
            ConditionPredicate(field="event.type", operator=ConditionOperator.EQUALS, value="success"),
        ],
    )
    assert ConditionEngine.evaluate_group(group_not, ctx) is True
