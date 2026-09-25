"""Unit tests for Offline Autonomy and Truthful Degraded Mode."""

import pytest
from core.ai.models import ProviderType
from core.ai.offline import OfflineManager
from core.ai.registry import ModelRegistry
from core.ai.router import ModelRouter


def test_offline_manager_force_offline_toggle():
    mgr = OfflineManager()
    assert mgr.is_forced_offline() is False

    mgr.set_force_offline(True)
    assert mgr.is_forced_offline() is True
    assert mgr.is_online() is False

    mgr.set_force_offline(False)
    assert mgr.is_forced_offline() is False


def test_offline_capability_validation():
    mgr = OfflineManager(force_offline=True)

    # Local capabilities should pass offline
    ok_fs, _ = mgr.validate_capability_offline("local_file_system")
    assert ok_fs is True

    ok_comp, _ = mgr.validate_capability_offline("computer_control")
    assert ok_comp is True

    # Web/Cloud capabilities must fail offline with an informative message
    ok_web, reason = mgr.validate_capability_offline("web_research")
    assert ok_web is False
    assert "requires active internet" in reason


def test_truthful_offline_planning_prevents_hallucination():
    mgr = OfflineManager(force_offline=True)

    # Real-time web inquiry
    resp = mgr.plan_offline_response("What is the latest news and stock price today?")
    assert resp is not None
    assert "Internet access is currently unavailable" in resp
    assert "local Knowledge OS" in resp

    # Local query should not be blocked
    resp_local = mgr.plan_offline_response("List files on my desktop")
    assert resp_local is None


def test_router_blocks_cloud_when_offline():
    reg = ModelRegistry()
    offline_mgr = OfflineManager(force_offline=True)
    router = ModelRouter(registry=reg, offline_mgr=offline_mgr)

    # General reasoning prompt that would normally permit cloud
    prompt = "Explain quantum computing algorithms in detail"
    decision = router.route(prompt)

    assert decision.constraints["allow_cloud"] is False
    assert decision.provider_type == ProviderType.LOCAL
