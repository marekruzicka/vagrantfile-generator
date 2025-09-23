"""
Contract test for GET /api/projects/{project_id} endpoint.

This test verifies the API contract specification for retrieving a specific project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from src.main import app

client = TestClient(app)


def test_get_project_success():
    """Test successful project retrieval."""
    # Arrange - First create a project
    create_data = {
        "name": "test-project",
        "description": "A test project"
    }
    create_response = client.post("/api/projects", json=create_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Act
    response = client.get(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "test-project"
    assert data["description"] == "A test project"
    assert data["version"] == "1.0.0"
    assert "created_at" in data
    assert "updated_at" in data
    assert isinstance(data["vms"], list)
    assert isinstance(data["global_plugins"], list)
    
    # Validate datetime format
    datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))


def test_get_project_with_vms():
    """Test project retrieval with VMs."""
    # This test will be more meaningful once VM creation is implemented
    # For now, just test the structure
    
    # Arrange - Create a project
    create_data = {"name": "project-with-vms"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act
    response = client.get(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert "vms" in data
    assert isinstance(data["vms"], list)
    
    # When VMs are present, each should have the expected structure
    for vm in data["vms"]:
        assert "name" in vm
        assert "box" in vm
        assert "hostname" in vm
        assert "memory" in vm
        assert "cpus" in vm
        assert "network_interfaces" in vm
        assert "synced_folders" in vm
        assert "provisioners" in vm
        assert "plugins" in vm
        assert isinstance(vm["network_interfaces"], list)
        assert isinstance(vm["synced_folders"], list)
        assert isinstance(vm["provisioners"], list)
        assert isinstance(vm["plugins"], list)


def test_get_project_not_found():
    """Test retrieving non-existent project."""
    # Arrange
    fake_id = str(uuid.uuid4())
    
    # Act
    response = client.get(f"/api/projects/{fake_id}")
    
    # Assert
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data


def test_get_project_invalid_uuid():
    """Test retrieving project with invalid UUID."""
    # Arrange
    invalid_ids = [
        "not-a-uuid",
        "123",
        "",
        "invalid-uuid-format"
    ]
    
    for invalid_id in invalid_ids:
        # Act
        response = client.get(f"/api/projects/{invalid_id}")
        
        # Assert
        # Should be 422 (validation error) or 404 depending on FastAPI path validation
        assert response.status_code in [404, 422]


def test_get_project_response_structure():
    """Test that the response has the exact required structure."""
    # Arrange
    create_data = {
        "name": "structure-test-project",
        "description": "Testing response structure"
    }
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act
    response = client.get(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    required_fields = [
        "id", "name", "description", "version", 
        "created_at", "updated_at", "vms", "global_plugins"
    ]
    
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"
    
    # Validate types
    assert isinstance(data["id"], str)
    assert isinstance(data["name"], str)
    assert isinstance(data["description"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["created_at"], str)
    assert isinstance(data["updated_at"], str)
    assert isinstance(data["vms"], list)
    assert isinstance(data["global_plugins"], list)


def test_get_project_content_type():
    """Test that the response has correct content type."""
    # Arrange
    create_data = {"name": "content-type-test"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act
    response = client.get(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")