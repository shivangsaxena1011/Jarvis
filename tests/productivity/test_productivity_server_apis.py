"""
Unit tests for Phase 16 Desktop Server REST APIs.
"""

from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from apps.desktop.server import app, orchestrator


@pytest.mark.asyncio
async def test_productivity_rest_apis(tmp_path: Path):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Dashboard
        res = await client.get("/api/productivity/dashboard")
        assert res.status_code == 200
        data = res.json()
        assert "active_tasks_count" in data

        # 2. Create Project
        p_res = await client.post("/api/projects", json={
            "name": "REST API Test Project",
            "description": "Testing desktop endpoints",
            "priority": "HIGH",
        })
        assert p_res.status_code == 200
        p_data = p_res.json()
        proj_id = p_data["id"]

        # 3. Create Task
        t_res = await client.post("/api/tasks", json={
            "title": "REST API Task",
            "project_id": proj_id,
            "priority": "CRITICAL",
            "estimated_duration_minutes": 45,
        })
        assert t_res.status_code == 200
        t_data = t_res.json()
        task_id = t_data["id"]

        # 4. Project Context
        ctx_res = await client.get(f"/api/projects/{proj_id}/context")
        assert ctx_res.status_code == 200
        assert ctx_res.json()["project_name"] == "REST API Test Project"

        # 5. Planning
        plan_res = await client.post("/api/planning/daily", json={"available_hours": 6.0})
        assert plan_res.status_code == 200
        assert "plan" in plan_res.json()

        # 6. Complete Task
        comp_res = await client.post(f"/api/tasks/{task_id}/complete", json={"notes": "All done via test"})
        assert comp_res.status_code == 200
        assert comp_res.json()["status"] == "COMPLETED"
