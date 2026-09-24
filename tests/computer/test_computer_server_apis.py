"""
Unit tests for Phase 17 Desktop Server REST APIs for Computer Autonomy.
"""

from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from apps.desktop.server import app, orchestrator


@pytest.mark.asyncio
async def test_computer_autonomy_rest_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Observe
        obs_res = await client.post("/api/computer/observe", json={"capture_image": False})
        assert obs_res.status_code == 200
        obs_data = obs_res.json()
        assert "monitors" in obs_data

        # 2. State
        state_res = await client.get("/api/computer/state")
        assert state_res.status_code == 200
        assert "emergency_stopped" in state_res.json()

        # 3. Windows list
        win_res = await client.get("/api/computer/windows")
        assert win_res.status_code == 200
        assert isinstance(win_res.json(), list)

        # 4. Plan
        plan_res = await client.post("/api/computer/plan", json={"goal": "Organize downloads"})
        assert plan_res.status_code == 200
        assert "steps" in plan_res.json()

        # 5. Act
        act_res = await client.post(
            "/api/computer/act",
            json={"action_type": "type", "parameters": {"text": "hello"}},
        )
        assert act_res.status_code == 200

        # 6. Stop
        stop_res = await client.post("/api/computer/stop")
        assert stop_res.status_code == 200
        assert stop_res.json()["emergency_stopped"] is True

        # Reset emergency stop for subsequent tests
        orchestrator.computer_autonomy.lock_manager.reset_emergency_stop()
