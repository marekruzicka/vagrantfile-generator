"""
Contract test for POST /api/projects/{project_id}/generate endpoint.

This test verifies the API contract specification for generating Vagrantfiles.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)


def test_generate_vagrantfile_success():
    """Test successful Vagrantfile generation."""
    # Arrange - Create project with VMs
    create_project = client.post("/api/projects", json={"name": "generation-test"})
    project_id = create_project.json()["id"]
    
    # Add VM to project
    vm_data = {
        "name": "web",
        "box": "ubuntu/jammy64",
        "hostname": "web",
        "memory": 2048,
        "cpus": 2
    }
    create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert create_vm.status_code == 201
    
    # Act
    response = client.post(f"/api/projects/{project_id}/generate")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert "content" in data
    assert "filename" in data
    assert "validation" in data
    
    assert data["filename"] == "Vagrantfile"
    assert isinstance(data["content"], str)
    assert len(data["content"]) > 0
    
    # Check validation structure
    validation = data["validation"]
    assert "is_valid" in validation
    assert "errors" in validation
    assert "warnings" in validation
    assert isinstance(validation["is_valid"], bool)
    assert isinstance(validation["errors"], list)
    assert isinstance(validation["warnings"], list)


def test_generate_vagrantfile_empty_project():
    """Test generating Vagrantfile for project with no VMs."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "empty-project"})
    project_id = create_project.json()["id"]
    
    # Act
    response = client.post(f"/api/projects/{project_id}/generate")
    
    # Assert
    # Should either succeed with minimal Vagrantfile or return validation error
    assert response.status_code in [200, 400]
    
    if response.status_code == 200:
        data = response.json()
        assert data["validation"]["is_valid"] == False
        assert len(data["validation"]["errors"]) > 0


def test_generate_vagrantfile_project_not_found():
    """Test generating Vagrantfile for non-existent project."""
    # Arrange
    fake_project_id = str(uuid.uuid4())
    
    # Act
    response = client.post(f"/api/projects/{fake_project_id}/generate")
    
    # Assert
    assert response.status_code == 404


def test_generate_vagrantfile_contains_vm_config():
    """Test that generated Vagrantfile contains VM configuration."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "vm-config-test"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "test-vm",
        "box": "ubuntu/focal64",
        "hostname": "test-host",
        "memory": 4096,
        "cpus": 4
    }
    create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert create_vm.status_code == 201
    
    # Act
    response = client.post(f"/api/projects/{project_id}/generate")
    
    # Assert
    assert response.status_code == 200
    
    content = response.json()["content"]
    
    # Check that VM configuration is in the generated content
    assert "test-vm" in content
    assert "ubuntu/focal64" in content
    assert "test-host" in content
    assert "4096" in content
    assert "4" in content


def test_generate_vagrantfile_multiple_vms():
    """Test generating Vagrantfile with multiple VMs."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "multi-vm-test"})
    project_id = create_project.json()["id"]
    
    vms = [
        {"name": "web", "box": "ubuntu/jammy64", "memory": 2048, "cpus": 2},
        {"name": "db", "box": "ubuntu/focal64", "memory": 4096, "cpus": 4},
        {"name": "cache", "box": "centos/7", "memory": 1024, "cpus": 1}
    ]
    
    for vm_data in vms:
        create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
        assert create_vm.status_code == 201
    
    # Act
    response = client.post(f"/api/projects/{project_id}/generate")
    
    # Assert
    assert response.status_code == 200
    
    content = response.json()["content"]
    
    # All VMs should be in the generated content
    for vm in vms:
        assert vm["name"] in content
        assert vm["box"] in content