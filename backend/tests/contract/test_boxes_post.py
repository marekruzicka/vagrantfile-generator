"""
Contract tests for POST /api/boxes
"""

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_create_box_minimal():
    payload = {
        "name": "box-test",
        "description": "Box test",
        "provider": "libvirt"
    }

    response = client.post("/api/boxes", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert data["provider"] == payload["provider"]
    assert "is_shared" in data
    assert data["is_shared"] is False
    assert data.get("owner_id") is None
