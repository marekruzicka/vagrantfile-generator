"""
Contract tests for Network Interface PUT endpoint.

These tests verify the API contract for updating network interfaces on VMs.
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_data():
    """Clean test data before each test."""
    import shutil
    import os
    data_dir = "data"
    if os.path.exists(data_dir):
        try:
            shutil.rmtree(data_dir)
        except OSError:
            # Handle case where directory is busy (in containers)
            pass


def test_update_network_interface_success():
    """Test successfully updating a network interface."""
    # Create project, VM, and interface
    project_data = {"name": "update-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface first
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"
    }
    add_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    interface = add_response.json()
    interface_id = interface.get("id", "interface-1")  # Fallback ID
    
    # Update the interface
    update_data = {
        "ip_address": "192.168.1.150",
        "netmask": "255.255.0.0"
    }
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    assert response.headers.get("content-type") == "application/json"
    
    data = response.json()
    assert data["ip_address"] == "192.168.1.150"
    assert data["netmask"] == "255.255.0.0"


def test_update_network_interface_partial():
    """Test updating only some fields of a network interface."""
    # Setup
    project_data = {"name": "partial-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100",
        "netmask": "255.255.255.0"
    }
    add_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    interface = add_response.json()
    interface_id = interface.get("id", "interface-1")
    
    # Update only IP address
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["ip_address"] == "192.168.1.200"
    assert data["netmask"] == "255.255.255.0"  # Should remain unchanged


def test_update_network_interface_not_found():
    """Test updating a non-existent network interface."""
    # Create project and VM
    project_data = {"name": "not-found-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Try to update non-existent interface
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/non-existent",
        json=update_data
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    assert "Network interface 'non-existent' not found" in error_data["detail"]


def test_update_network_interface_project_not_found():
    """Test updating interface in non-existent project."""
    fake_uuid = str(uuid.uuid4())
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        f"/api/projects/{fake_uuid}/vms/test-vm/network-interfaces/interface-1",
        json=update_data
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_update_network_interface_vm_not_found():
    """Test updating interface on non-existent VM."""
    # Create project but no VM
    project_data = {"name": "no-vm-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/non-existent-vm/network-interfaces/interface-1",
        json=update_data
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    assert "VM 'non-existent-vm' not found" in error_data["detail"]


def test_update_network_interface_invalid_data():
    """Test updating interface with invalid data."""
    # Setup
    project_data = {"name": "invalid-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"
    }
    add_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    interface = add_response.json()
    interface_id = interface.get("id", "interface-1")
    
    # Invalid update data (invalid IP)
    update_data = {"ip_address": "invalid-ip"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}",
        json=update_data
    )
    
    # This might be 422 (validation error) or 400 (business logic error)
    assert response.status_code in [400, 422]
    error_data = response.json()
    assert "detail" in error_data


def test_update_network_interface_invalid_project_id():
    """Test updating interface with invalid project ID format."""
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        "/api/projects/invalid-uuid/vms/test-vm/network-interfaces/interface-1",
        json=update_data
    )
    
    assert response.status_code == 422  # FastAPI path validation
    error_data = response.json()
    assert "detail" in error_data


def test_update_network_interface_response_structure():
    """Test that update response has correct structure."""
    # Setup
    project_data = {"name": "structure-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"
    }
    add_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    interface = add_response.json()
    interface_id = interface.get("id", "interface-1")
    
    # Update
    update_data = {"ip_address": "192.168.1.200"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check required fields
    assert "type" in data
    assert "ip_assignment" in data
    assert "ip_address" in data
    assert data["ip_address"] == "192.168.1.200"


def test_update_network_interface_content_type():
    """Test that response has correct content type."""
    # Setup
    project_data = {"name": "content-type-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    add_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    interface = add_response.json()
    interface_id = interface.get("id", "interface-1")
    
    # Update
    update_data = {"ip_assignment": "static", "ip_address": "192.168.1.100"}
    
    response = client.put(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}",
        json=update_data
    )
    
    assert response.status_code == 200
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"