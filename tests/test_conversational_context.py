"""
Unit tests for SHIVANI Multi-Turn Conversational Context & Uncertainty Handling.
"""

from core.context.conversational import ConversationalContext


def test_conversational_turn_recording():
    ctx = ConversationalContext()
    ctx.record_turn(role="user", text="Chrome kholo")

    assert len(ctx.turns) == 1
    assert ctx.active_app == "chrome"
    assert ctx.active_domain == "browser"


def test_multi_turn_followup_resolution():
    ctx = ConversationalContext()

    # Turn 1: Open Chrome
    q1 = ctx.resolve_followup("Chrome kholo")
    ctx.record_turn("user", q1)
    assert ctx.active_app == "chrome"

    # Turn 2: Follow-up command "YouTube kholo" (binds to active Chrome context)
    q2 = ctx.resolve_followup("YouTube kholo")
    assert "in Chrome" in q2
    ctx.record_turn("user", q2)
    assert ctx.active_domain == "youtube"

    # Turn 3: Follow-up command "Arijit Singh search karo" (binds to active YouTube domain)
    q3 = ctx.resolve_followup("Arijit Singh search karo")
    assert "In YouTube" in q3

    # Turn 4: Deictic reference "isko band karo"
    q4 = ctx.resolve_followup("isko band karo")
    assert "close chrome" in q4


def test_uncertainty_clarification():
    ctx = ConversationalContext()

    # Confident recognition -> None (execute directly)
    no_clarif = ctx.check_uncertainty_clarification("Open Chrome", confidence=0.92, threshold=0.65)
    assert no_clarif is None

    # Low-confidence recognition -> Clarification prompt in Hindi
    clarif = ctx.check_uncertainty_clarification("Chrome kholo", confidence=0.45, threshold=0.65)
    assert clarif is not None
    assert "क्या आपने कहा कि" in clarif
    assert "Chrome kholo" in clarif
