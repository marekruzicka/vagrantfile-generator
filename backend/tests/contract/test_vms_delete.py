"""
Contract test for DELETE /api/projects/{project_id}/vms/{vm_name} endpoint.

This test verifies the API contract specification for deleting VMs from a project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)


def test_delete_vm_success():
    """Test successful VM deletion."""
    # Arrange - Create project and VM
    create_project = client.post("/api/projects", json={"name": "vm-delete-project"})
    project_id = create_project.json()["id"]
    
    vm_data = {
        "name": "vm-to-delete",
        "box": "ubuntu/jammy64"
    }
    
    create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert create_vm.status_code == 201
    
    # Verify VM exists
    get_project = client.get(f"/api/projects/{project_id}")
    assert len(get_project.json()["vms"]) == 1
    
    # Act
    response = client.delete(f"/api/projects/{project_id}/vms/vm-to-delete")
    
    # Assert
    assert response.status_code == 204
    assert response.content == b""
    
    # Verify VM is deleted
    updated_project = client.get(f"/api/projects/{project_id}")
    assert len(updated_project.json()["vms"]) == 0


def test_delete_vm_not_found():
    """Test deleting non-existent VM."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "vm-not-found-project"})
    project_id = create_project.json()["id"]
    
    # Act
    response = client.delete(f"/api/projects/{project_id}/vms/non-existent-vm")
    
    # Assert
    assert response.status_code == 404


def test_delete_vm_project_not_found():
    """Test deleting VM from non-existent project."""
    # Arrange
    fake_project_id = str(uuid.uuid4())
    
    # Act
    response = client.delete(f"/api/projects/{fake_project_id}/vms/some-vm")
    
    # Assert
    assert response.status_code == 404


def test_delete_vm_multiple_vms():
    """Test deleting one VM when project has multiple VMs."""
    # Arrange
    create_project = client.post("/api/projects", json={"name": "multi-vm-project"})
    project_id = create_project.json()["id"]
    
    # Create multiple VMs
    vm_names = ["vm1", "vm2", "vm3"]
    for vm_name in vm_names:
        vm_data = {"name": vm_name, "box": "ubuntu/jammy64"}
        create_vm = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
        assert create_vm.status_code == 201
    
    # Verify all VMs exist
    get_project = client.get(f"/api/projects/{project_id}")
    assert len(get_project.json()["vms"]) == 3
    
    # Act - Delete middle VM
    response = client.delete(f"/api/projects/{project_id}/vms/vm2")
    
    # Assert
    assert response.status_code == 204
    
    # Verify only vm2 is deleted
    updated_project = client.get(f"/api/projects/{project_id}")
    project_data = updated_project.json()
    assert len(project_data["vms"]) == 2
    
    remaining_vm_names = [vm["name"] for vm in project_data["vms"]]
    assert "vm1" in remaining_vm_names
    assert "vm2" not in remaining_vm_names  # Should be deleted
    assert "vm3" in remaining_vm_names