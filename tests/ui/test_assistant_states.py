"""
Tests for Assistant State Machine, Privacy Mode, and Lock screen logic.
"""

import pytest
from apps.desktop.server import AssistantState, AssistantStateManager
from core.events.bus import Event, EventType


def test_assistant_state_transitions():
    mgr = AssistantStateManager()
    assert mgr.state == AssistantState.IDLE

    mgr.set_state(AssistantState.LISTENING)
    assert mgr.state == AssistantState.LISTENING

    mgr.set_state(AssistantState.PLANNING, agent="Planner", step="Decomposing task")
    assert mgr.state == AssistantState.PLANNING
    assert mgr.current_agent == "Planner"
    assert mgr.current_step == "Decomposing task"

    mgr.set_state(AssistantState.EXECUTING, agent="Computer Agent", step="Opening Chrome")
    assert mgr.state == AssistantState.EXECUTING
    assert mgr.current_agent == "Computer Agent"

    mgr.set_state(AssistantState.WAITING_FOR_PERMISSION)
    assert mgr.state == AssistantState.WAITING_FOR_PERMISSION

    mgr.set_state(AssistantState.COMPLETED)
    assert mgr.state == AssistantState.COMPLETED


def test_privacy_mode_toggle():
    mgr = AssistantStateManager()
    assert mgr.privacy_mode is False

    is_on = mgr.toggle_privacy_mode()
    assert is_on is True
    assert mgr.privacy_mode is True

    is_off = mgr.toggle_privacy_mode(False)
    assert is_off is False
    assert mgr.privacy_mode is False


def test_lock_and_unlock_security():
    mgr = AssistantStateManager()
    assert mgr.locked is False

    mgr.set_lock_code("1234")
    mgr.lock()
    assert mgr.locked is True
    assert mgr.state == AssistantState.LOCKED

    # State cannot change while locked
    mgr.set_state(AssistantState.EXECUTING)
    assert mgr.state == AssistantState.LOCKED

    # Unlock with wrong pin
    bad_unlocked = mgr.unlock("wrong_code")
    assert bad_unlocked is False
    assert mgr.locked is True

    # Unlock with correct pin
    unlocked = mgr.unlock("1234")
    assert unlocked is True
    assert mgr.locked is False
    assert mgr.state == AssistantState.IDLE
