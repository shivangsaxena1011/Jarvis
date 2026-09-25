"""Unit tests for Phase 19 AI Server REST APIs (/api/ai/*)."""

import pytest
from fastapi.testclient import TestClient

from apps.desktop.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_ai_status(client):
    res = client.get("/api/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "routing_strategy" in data
    assert "hardware" in data
    assert "local_runtime_available" in data
    assert "installed_local_models" in data
    assert "metrics" in data


def test_api_ai_models_and_filter(client):
    res = client.get("/api/ai/models")
    assert res.status_code == 200
    data = res.json()
    assert "models" in data
    assert data["total"] >= 10

    # Filter by local provider
    res_local = client.get("/api/ai/models?provider=local")
    assert res_local.status_code == 200
    local_data = res_local.json()
    assert all(m["provider_type"] == "local" for m in local_data["models"])


def test_api_ai_route_deterministic_math(client):
    res = client.post(
        "/api/ai/route",
        json={"query": "calculate 500 * 20"},
    )
    assert res.status_code == 200
    data = res.json()["decision"]
    assert data["selected_model_id"] == "deterministic-calc"
    assert data["is_deterministic"] is True


def test_api_ai_doctor(client):
    res = client.get("/api/ai/doctor")
    assert res.status_code == 200
    data = res.json()
    assert "diagnostics" in data
    assert "report" in data
    assert "SHIVANI AI DOCTOR DIAGNOSTIC REPORT" in data["report"]


def test_api_ai_benchmark(client):
    res = client.post(
        "/api/ai/benchmark",
        json={"model_id": "phi3:mini"},
    )
    assert res.status_code == 200
    data = res.json()["benchmark"]
    assert data["model_id"] == "phi3:mini"
    assert data["tokens_per_second"] > 0.0


def test_api_ai_usage_metrics(client):
    res = client.get("/api/ai/usage")
    assert res.status_code == 200
    data = res.json()
    assert "usage" in data
    assert "total_requests" in data["usage"]


def test_api_ai_offline_toggle(client):
    # Query status
    res = client.get("/api/ai/offline")
    assert res.status_code == 200
    assert "is_online" in res.json()

    # Force offline
    res_set = client.post("/api/ai/offline", json={"force_offline": True})
    assert res_set.status_code == 200
    assert res_set.json()["forced_offline"] is True
    assert res_set.json()["is_online"] is False

    # Restore online
    res_restore = client.post("/api/ai/offline", json={"force_offline": False})
    assert res_restore.status_code == 200
    assert res_restore.json()["forced_offline"] is False
