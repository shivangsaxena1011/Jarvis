"""
Unit tests for Phase 14 desktop server REST and state endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from apps.desktop.server import app, assistant_state_mgr, AssistantState


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_server_status_and_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/status")
        assert res.status_code == 200
        data = res.json()
        assert data["agent_name"] == "SHIVANI"
        assert "registered_tools_count" in data
        assert data["registered_tools_count"] >= 159


@pytest.mark.asyncio
async def test_assistant_state_control_privacy_and_lock():
    assistant_state_mgr.set_lock_code("1234")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Privacy toggle
        res = await client.post("/api/state/control", json={"action": "privacy_toggle", "enabled": True})
        assert res.status_code == 200
        assert res.json()["privacy_mode"] is True

        # Toggle back
        res_off = await client.post("/api/state/control", json={"action": "privacy_toggle", "enabled": False})
        assert res_off.status_code == 200
        assert res_off.json()["privacy_mode"] is False

        # 2. Lock assistant
        res_lock = await client.post("/api/state/control", json={"action": "lock"})
        assert res_lock.status_code == 200
        assert res_lock.json()["locked"] is True

        # Verify task submission is blocked while locked (423 Locked)
        res_blocked = await client.post("/api/tasks", json={"query": "test query"})
        assert res_blocked.status_code == 423

        # 3. Unlock with wrong PIN
        res_bad_pin = await client.post("/api/state/control", json={"action": "unlock", "pin": "9999"})
        assert res_bad_pin.status_code == 401

        # Unlock with valid PIN
        res_unlock = await client.post("/api/state/control", json={"action": "unlock", "pin": "1234"})
        assert res_unlock.status_code == 200
        assert res_unlock.json()["locked"] is False


@pytest.mark.asyncio
async def test_conversation_message_and_tasks():
    assistant_state_mgr.locked = False
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit conversation message
        res = await client.post("/api/conversation/message", json={"message": "Shivani, check status."})
        assert res.status_code == 200
        data = res.json()
        assert "task_id" in data
        task_id = data["task_id"]

        # Get task timeline
        timeline_res = await client.get(f"/api/tasks/{task_id}/timeline")
        assert timeline_res.status_code == 200
        tdata = timeline_res.json()
        assert tdata["task_id"] == task_id
        assert "query" in tdata


@pytest.mark.asyncio
async def test_skills_and_connectors_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Skills
        res_skills = await client.get("/api/skills")
        assert res_skills.status_code == 200
        assert isinstance(res_skills.json(), list)

        # Connectors
        res_conns = await client.get("/api/connectors")
        assert res_conns.status_code == 200
        assert isinstance(res_conns.json(), list)

        # Adapters
        res_adapters = await client.get("/api/adapters")
        assert res_adapters.status_code == 200
        assert isinstance(res_adapters.json(), list)


@pytest.mark.asyncio
async def test_devices_and_knowledge_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Devices
        res_dev = await client.get("/api/devices")
        assert res_dev.status_code == 200
        assert isinstance(res_dev.json(), list)

        # Knowledge Search
        res_know = await client.get("/api/knowledge/search?q=test")
        assert res_know.status_code == 200
        assert isinstance(res_know.json(), list)

        # Add Note
        res_note = await client.post("/api/knowledge/notes", json={
            "title": "API Test Note",
            "content": "Testing Knowledge OS REST API",
            "tags": ["test"],
        })
        assert res_note.status_code == 200
        assert res_note.json()["title"] == "API Test Note"


@pytest.mark.asyncio
async def test_memory_and_notifications_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Set preference
        res_pref = await client.post("/api/memory/preferences", json={"key": "theme", "value": "dark"})
        assert res_pref.status_code == 200

        # Notifications
        res_notif = await client.get("/api/notifications")
        assert res_notif.status_code == 200
        assert isinstance(res_notif.json(), list)


@pytest.mark.asyncio
async def test_security_and_diagnostics_apis():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Security status
        res_sec = await client.get("/api/security/status")
        assert res_sec.status_code == 200
        sdata = res_sec.json()
        assert "permission_policy" in sdata

        # Diagnostics doctor run
        res_diag = await client.get("/api/diagnostics/run?full=false")
        assert res_diag.status_code == 200
        ddata = res_diag.json()
        assert "passed" in ddata
        assert "items" in ddata
