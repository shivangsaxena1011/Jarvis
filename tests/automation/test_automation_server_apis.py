"""
Unit tests for Phase 15 Desktop Automation REST Endpoints.
"""

import pytest
from httpx import AsyncClient, ASGITransport

from apps.desktop.server import app


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_automation_rest_crud_and_templates():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List automations
        res_list = await client.get("/api/automations")
        assert res_list.status_code == 200
        automations = res_list.json()
        assert isinstance(automations, list)
        assert len(automations) >= 7

        # 2. Get templates
        res_tpl = await client.get("/api/automations/templates")
        assert res_tpl.status_code == 200
        templates = res_tpl.json()
        assert len(templates) >= 7

        # 3. Create from prompt
        res_create = await client.post("/api/automations/create_prompt", json={
            "prompt": "Every Monday at 9 AM, review my open GitHub issues"
        })
        assert res_create.status_code == 200
        cdata = res_create.json()
        assert cdata["success"] is True
        auto_id = cdata["automation"]["id"]

        # 4. Get specific automation
        res_get = await client.get(f"/api/automations/{auto_id}")
        assert res_get.status_code == 200
        assert res_get.json()["id"] == auto_id

        # 5. Pause and Resume
        res_pause = await client.post(f"/api/automations/{auto_id}/pause")
        assert res_pause.status_code == 200
        assert res_pause.json()["status"] == "PAUSED"

        res_resume = await client.post(f"/api/automations/{auto_id}/resume")
        assert res_resume.status_code == 200
        assert res_resume.json()["status"] == "ACTIVE"

        # 6. Run dry run
        res_run = await client.post(f"/api/automations/{auto_id}/run", json={"dry_run": True})
        assert res_run.status_code == 200
        assert res_run.json()["status"] == "COMPLETED"

        # 7. Analytics
        res_analytics = await client.get("/api/automations/analytics")
        assert res_analytics.status_code == 200
        adata = res_analytics.json()
        assert "total_automations" in adata
        assert "success_rate" in adata

        # 8. Delete
        res_del = await client.delete(f"/api/automations/{auto_id}")
        assert res_del.status_code == 200
        assert res_del.json()["success"] is True
