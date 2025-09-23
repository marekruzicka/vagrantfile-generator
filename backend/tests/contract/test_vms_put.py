"""
Contract test for PUT /api/projects/{project_id}/vms/{vm_name} endpoint.

This test verifies the API contract specification for updating VMs in a project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)


def test_update_vm_success():
    """Test successful VM update."""
    # Arrange - Create project and VM
    create_project = client.post("/api/projects", json={"name": "vm-update-project"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "test-vm",
        "box": "ubuntu/jammy64",
        "memory": 1024,
        "cpus": 1
    }
    
    create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert create_vm.status_code == 201
    
    # Update VM data
    updated_vm_data = {
        "name": "test-vm",
        "box": "ubuntu/focal64",  # Changed box
        "hostname": "updated-hostname",
        "memory": 2048,  # Increased memory
        "cpus": 2  # Increased CPUs
    }
    
    # Act
    response = client.put(f"/api/projects/{project_id}/vms/test-vm", json=updated_vm_data)
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "test-vm"
    assert data["box"] == "ubuntu/focal64"
    assert data["hostname"] == "updated-hostname"
    assert data["memory"] == 2048
    assert data["cpus"] == 2


def test_update_vm_not_found():
    """Test updating non-existent VM."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "vm-not-found-project"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "non-existent-vm",
        "box": "ubuntu/jammy64"
    }
    
    # Act
    response = client.put(f"/api/projects/{project_id}/vms/non-existent-vm", json=vm_data)
    
    # Assert
    assert response.status_code == 404


def test_update_vm_project_not_found():
    """Test updating VM in non-existent project."""
    # Arrange
    fake_project_id = str(uuid.uuid4())
    vm_data = {
        "name": "test-vm",
        "box": "ubuntu/jammy64"
    }
    
    # Act
    response = client.put(f"/api/projects/{fake_project_id}/vms/test-vm", json=vm_data)
    
    # Assert
    assert response.status_code == 404


def test_update_vm_invalid_data():
    """Test updating VM with invalid data."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "invalid-update-project"})
    project_id = create_project.json()["id"]
    
    # Create VM first
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert create_vm.status_code == 201
    
    invalid_updates = [
        {"name": "", "box": "ubuntu/jammy64"},  # Empty name
        {"name": "test-vm", "box": ""},  # Empty box
        {"name": "test-vm", "box": "ubuntu/jammy64", "memory": -1},  # Invalid memory
        {"name": "test-vm", "box": "ubuntu/jammy64", "cpus": 0},  # Invalid cpus
        {}  # Empty object
    ]
    
    for invalid_data in invalid_updates:
        # Act
        response = client.put(f"/api/projects/{project_id}/vms/test-vm", json=invalid_data)
        
        # Assert
        assert response.status_code == 400