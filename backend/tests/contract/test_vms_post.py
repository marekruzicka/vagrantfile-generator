"""
Contract test for POST /api/projects/{project_id}/vms endpoint.

This test verifies the API contract specification for adding VMs to a project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)


def test_add_vm_success():
    """Test successful VM addition to project."""
    # Arrange - Create a project first
    create_project = client.post("/api/projects", json={"name": "vm-test-project"})
    assert create_project.status_code == 201
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "web-server",
        "box": "ubuntu/jammy64",
        "hostname": "web",
        "memory": 2048,
        "cpus": 2
    }
    
    # Act
    response = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Assert
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "web-server"
    assert data["box"] == "ubuntu/jammy64"
    assert data["hostname"] == "web"
    assert data["memory"] == 2048
    assert data["cpus"] == 2
    assert data["network_interfaces"] == []
    assert data["synced_folders"] == []
    assert data["provisioners"] == []
    assert data["plugins"] == []


def test_add_vm_minimal_data():
    """Test VM addition with minimal required data."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "minimal-vm-project"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "minimal-vm",
        "box": "ubuntu/jammy64"
        # No hostname, memory, or cpus - should use defaults
    }
    
    # Act
    response = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Assert
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "minimal-vm"
    assert data["box"] == "ubuntu/jammy64"
    assert data["hostname"] == "minimal-vm"  # Should default to name
    assert data["memory"] == 1024  # Default memory
    assert data["cpus"] == 1  # Default cpus


def test_add_vm_project_not_found():
    """Test adding VM to non-existent project."""
    # Arrange
    fake_project_id = str(uuid.uuid4())
    vm_data = {
        "name": "test-vm",
        "box": "ubuntu/jammy64"
    }
    
    # Act
    response = client.post(f"/api/projects/{fake_project_id}/vms", json=vm_data)
    
    # Assert
    assert response.status_code == 404


def test_add_vm_duplicate_name():
    """Test adding VM with duplicate name in same project."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "duplicate-vm-project"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "duplicate-vm",
        "box": "ubuntu/jammy64"
    }
    
    # Add VM first time
    response1 = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert response1.status_code == 201
    
    # Act - Try to add VM with same name
    response2 = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Assert
    assert response2.status_code == 409


def test_add_vm_invalid_data():
    """Test adding VM with invalid data."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "invalid-vm-project"})
    project_id = create_project.json()["id"]
    
    invalid_data_cases = [
        {"name": "", "box": "ubuntu/jammy64"},  # Empty name
        {"name": None, "box": "ubuntu/jammy64"},  # Null name
        {"name": "test-vm", "box": ""},  # Empty box
        {"name": "test-vm", "box": None},  # Null box
        {"name": "test-vm"},  # Missing box
        {"box": "ubuntu/jammy64"},  # Missing name
        {"name": "test-vm", "box": "ubuntu/jammy64", "memory": -1},  # Invalid memory
        {"name": "test-vm", "box": "ubuntu/jammy64", "cpus": 0},  # Invalid cpus
        {"name": "test-vm", "box": "ubuntu/jammy64", "memory": "not-a-number"},  # Invalid memory type
        {}  # Empty object
    ]
    
    for invalid_data in invalid_data_cases:
        # Act
        response = client.post(f"/api/projects/{project_id}/vms", json=invalid_data)
        
        # Assert
        assert response.status_code == 400


def test_add_vm_invalid_project_id():
    """Test adding VM with invalid project ID."""
    vm_data = {
        "name": "test-vm",
        "box": "ubuntu/jammy64"
    }
    
    invalid_ids = ["not-a-uuid", "123", ""]
    
    for invalid_id in invalid_ids:
        # Act
        response = client.post(f"/api/projects/{invalid_id}/vms", json=vm_data)
        
        # Assert
        assert response.status_code in [404, 422]  # Depends on FastAPI path validation


def test_add_vm_updates_project():
    """Test that adding a VM updates the project's VM list."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "update-test-project"})
    project_id = create_project.json()["id"]
    
    # Verify project initially has no VMs
    get_project = client.get(f"/api/projects/{project_id}")
    assert len(get_project.json()["vms"]) == 0
    
    vm_data = {
        "name": "new-vm",
        "box": "ubuntu/jammy64"
    }
    
    # Act
    response = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert response.status_code == 201
    
    # Assert - Check project now has the VM
    updated_project = client.get(f"/api/projects/{project_id}")
    assert updated_project.status_code == 200
    
    project_data = updated_project.json()
    assert len(project_data["vms"]) == 1
    assert project_data["vms"][0]["name"] == "new-vm"