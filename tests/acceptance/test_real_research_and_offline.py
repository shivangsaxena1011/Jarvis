"""
Real-World Acceptance Test: Research & Offline Truthful Degradation.
Tests live search capability when online, and strict truthful degradation
and refusal without hallucination when offline mode is activated.
"""

import pytest
from core.ai.offline import OfflineManager
from integrations.research.service import ResearchService
from tools.integrations.research_tools import ResearchSearchTool


@pytest.mark.asyncio
async def test_offline_manager_honest_degradation():
    """Verify OfflineManager blocks web-dependent capabilities and answers truthfully."""
    offline_mgr = OfflineManager()
    
    # 1. Host is actually online right now
    assert offline_mgr.is_online() is True
    ok, err = offline_mgr.validate_capability_offline("web_research")
    assert ok is True
    assert err is None
    
    # 2. Force offline mode
    offline_mgr.set_force_offline(True)
    try:
        assert offline_mgr.is_online() is False
        assert offline_mgr.is_forced_offline() is True
        
        # Validate capability refusal
        ok, err = offline_mgr.validate_capability_offline("web_research")
        assert ok is False
        assert "requires active internet access" in err
        assert "Internet is currently unavailable" in err
        
        # Validate local offline capabilities remain available
        ok_local, _ = offline_mgr.validate_capability_offline("computer_control")
        assert ok_local is True
        ok_local2, _ = offline_mgr.validate_capability_offline("local_file_system")
        assert ok_local2 is True
        
        # Test honest planning refusal without hallucination
        refusal = offline_mgr.plan_offline_response("search google for latest news")
        assert refusal is not None
        assert "Internet access is currently unavailable" in refusal
        assert "local Knowledge OS" in refusal
        
        # Test query that does not require internet returns None (allowed)
        no_refusal = offline_mgr.plan_offline_response("format local code in src")
        assert no_refusal is None
    finally:
        offline_mgr.set_force_offline(False)
        assert offline_mgr.is_online() is True


@pytest.mark.asyncio
async def test_real_research_service_or_structured_sources():
    """Verify research service returns valid structured source citations with provenance."""
    service = ResearchService()
    # Search query
    result = await service.search(query="Python asyncio architecture", limit=3)
    assert result is not None
    assert "sources" in result or "count" in result
    sources = result.get("sources", [])
    assert len(sources) > 0
    first_src = sources[0]
    assert "title" in first_src
    assert "url" in first_src
    assert "publisher" in first_src
    assert "snippet" in first_src
    assert "relevance" in first_src
