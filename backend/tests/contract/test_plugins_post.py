"""
Contract tests for POST /api/plugins
"""

from datetime import datetime
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_create_plugin_minimal():
    payload = {
        "name": "plugin-test",
        "description": "Just a test"
    }

    response = client.post("/api/plugins", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["name"] == payload["name"]
    assert "is_shared" in data
    assert data["is_shared"] is False
    # Self-hosted mode -> no owner
    assert data.get("owner_id") is None


def test_create_plugin_with_configuration():
    payload = {
        "name": "plugin-test-2",
        "configuration": "puts 'hello'"
    }

    response = client.post("/api/plugins", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["configuration"] == payload["configuration"]
