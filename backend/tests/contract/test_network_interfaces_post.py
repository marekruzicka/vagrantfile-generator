"""
Contract tests for Network Interface POST endpoint.

These tests verify the API contract for adding network interfaces to VMs.
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


def test_add_network_interface_success():
    """Test successfully adding a network interface to a VM."""
    # Create a project
    project_data = {
        "name": "network-test-project",
        "description": "Test project for network interfaces"
    }
    create_response = client.post("/api/projects", json=project_data)
    assert create_response.status_code == 201
    project = create_response.json()
    project_id = project["id"]
    
    # Add a VM
    vm_data = {
        "name": "web-server",
        "box": "ubuntu/jammy64",
        "memory": 2048,
        "cpus": 2
    }
    vm_response = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert vm_response.status_code == 201
    
    # Add network interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100",
        "netmask": "255.255.255.0"
    }
    
    response = client.post(
        f"/api/projects/{project_id}/vms/web-server/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 201
    assert response.headers.get("content-type") == "application/json"
    
    data = response.json()
    assert "type" in data
    assert data["type"] == "private_network"
    assert "ip_address" in data
    assert data["ip_address"] == "192.168.1.100"


def test_add_network_interface_dhcp():
    """Test adding a DHCP network interface."""
    # Create project and VM
    project_data = {"name": "dhcp-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add DHCP interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    
    response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["ip_assignment"] == "dhcp"
    assert data["ip_address"] is None


def test_add_network_interface_project_not_found():
    """Test adding interface to non-existent project."""
    fake_uuid = str(uuid.uuid4())
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    
    response = client.post(
        f"/api/projects/{fake_uuid}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_add_network_interface_vm_not_found():
    """Test adding interface to non-existent VM."""
    # Create project but no VM
    project_data = {"name": "no-vm-project", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    
    response = client.post(
        f"/api/projects/{project_id}/vms/non-existent-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    assert "VM 'non-existent-vm' not found" in error_data["detail"]


def test_add_network_interface_invalid_data():
    """Test adding interface with invalid data."""
    # Create project and VM
    project_data = {"name": "invalid-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Invalid interface data (missing required fields)
    interface_data = {
        "invalid_field": "value"
    }
    
    response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 422  # FastAPI validation error
    error_data = response.json()
    assert "detail" in error_data


def test_add_network_interface_invalid_project_id():
    """Test adding interface with invalid project ID format."""
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    
    response = client.post(
        "/api/projects/invalid-uuid/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 422  # FastAPI path validation
    error_data = response.json()
    assert "detail" in error_data


def test_add_network_interface_response_headers():
    """Test that response has correct headers."""
    # Create project and VM
    project_data = {"name": "headers-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    interface_data = {
        "type": "private_network",
        "ip_assignment": "dhcp"
    }
    
    response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    assert response.status_code == 201
    assert "content-type" in response.headers
    assert response.headers["content-type"] == "application/json"


def test_add_network_interface_updates_project():
    """Test that adding interface updates the project."""
    # Create project and VM
    project_data = {"name": "update-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add interface
    interface_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.50"
    }
    
    client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface_data
    )
    
    # Verify project was updated
    project_response = client.get(f"/api/projects/{project_id}")
    assert project_response.status_code == 200
    project = project_response.json()
    
    vm = project["vms"][0]
    assert len(vm["network_interfaces"]) == 1
    assert vm["network_interfaces"][0]["ip_address"] == "192.168.1.50"