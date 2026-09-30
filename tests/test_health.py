"""
Unit tests for SHIVANI Health System & Endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from apps.desktop.server import app, orchestrator

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def reset_state():
    if orchestrator.emergency.is_stopped:
        orchestrator.emergency.resume()
@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("healthy", "degraded")
        assert "components" in data
        assert data["components"]["runtime"] == "healthy"
        assert data["components"]["tools"] == "healthy"
        assert data["components"]["event_bus"] == "healthy"


@pytest.mark.asyncio
async def test_status_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["agent_name"] == "SHIVANI"
        assert data["registered_tools_count"] >= 10
