"""Tests for Phase 18: Desktop Server REST Endpoints (/api/devices/*)."""

import pytest
from fastapi.testclient import TestClient

from apps.desktop.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_devices_list(client):
    response = client.get("/api/devices/mesh")
    assert response.status_code == 200
    data = response.json()
    assert "devices" in data
    assert "total" in data
    assert data["total"] >= 1


def test_api_devices_pairing_flow(client):
    # 1. Initiate pairing
    init_res = client.post(
        "/api/devices/pair",
        json={"display_name": "API Tablet", "platform": "tablet"},
    )
    assert init_res.status_code == 200
    init_data = init_res.json()
    assert "session_id" in init_data
    assert "code" in init_data
    session_id = init_data["session_id"]
    code = init_data["code"]

    # 2. Confirm pairing
    confirm_res = client.post(
        "/api/devices/pair/confirm",
        json={"session_id": session_id, "code": code, "capabilities": ["files", "notifications"]},
    )
    assert confirm_res.status_code == 200
    dev_data = confirm_res.json()["device"]
    assert dev_data["trust_state"] == "trusted"
    device_id = dev_data["device_id"]

    # 3. Get device
    get_res = client.get(f"/api/devices/{device_id}")
    assert get_res.status_code == 200
    assert get_res.json()["device"]["device_id"] == device_id

    # 4. Revoke device
    revoke_res = client.post(
        f"/api/devices/{device_id}/trust",
        json={"action": "revoke"},
    )
    assert revoke_res.status_code == 200
    assert revoke_res.json()["success"]


def test_api_devices_route_and_ambient(client):
    # Route task
    route_res = client.post(
        "/api/devices/route",
        json={"task_description": "Run unit tests in VS Code", "preferred_platform": "windows"},
    )
    assert route_res.status_code == 200
    route_data = route_res.json()
    assert "selected_device_id" in route_data

    # Ambient state
    ambient_get = client.get("/api/devices/ambient/state")
    assert ambient_get.status_code == 200
    assert ambient_get.json()["zero_surveillance_enforced"]

    ambient_post = client.post(
        "/api/devices/ambient/state",
        json={"mode": "task_only"},
    )
    assert ambient_post.status_code == 200
    assert ambient_post.json()["ambient_state"] == "task_only"


def test_api_emergency_stop(client):
    res = client.post("/api/devices/emergency_stop", json={"reason": "Test emergency stop"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ABORTED_ALL"
