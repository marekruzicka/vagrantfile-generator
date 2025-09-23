"""
Contract tests for Network Interface DELETE endpoint.

These tests verify the API contract for removing network interfaces from VMs.
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


def test_delete_network_interface_success():
    """Test successfully deleting a network interface."""
    # Create project, VM, and interface
    project_data = {"name": "delete-test", "description": ""}
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
    
    # Delete the interface
    response = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}"
    )
    
    assert response.status_code == 204
    assert response.content == b""  # No content for 204


def test_delete_network_interface_not_found():
    """Test deleting a non-existent network interface."""
    # Create project and VM
    project_data = {"name": "not-found-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Try to delete non-existent interface
    response = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/non-existent"
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    assert "Network interface 'non-existent' not found" in error_data["detail"]


def test_delete_network_interface_project_not_found():
    """Test deleting interface from non-existent project."""
    fake_uuid = str(uuid.uuid4())
    
    response = client.delete(
        f"/api/projects/{fake_uuid}/vms/test-vm/network-interfaces/interface-1"
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data


def test_delete_network_interface_vm_not_found():
    """Test deleting interface from non-existent VM."""
    # Create project but no VM
    project_data = {"name": "no-vm-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    response = client.delete(
        f"/api/projects/{project_id}/vms/non-existent-vm/network-interfaces/interface-1"
    )
    
    assert response.status_code == 404
    error_data = response.json()
    assert "detail" in error_data
    assert "VM 'non-existent-vm' not found" in error_data["detail"]


def test_delete_network_interface_multiple_interfaces():
    """Test deleting one interface when VM has multiple interfaces."""
    # Setup
    project_data = {"name": "multi-interface-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add first interface
    interface1_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"
    }
    add1_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface1_data
    )
    interface1 = add1_response.json()
    interface1_id = interface1.get("id", "interface-1")
    
    # Add second interface
    interface2_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.101"
    }
    add2_response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces",
        json=interface2_data
    )
    interface2 = add2_response.json()
    interface2_id = interface2.get("id", "interface-2")
    
    # Delete first interface
    response = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface1_id}"
    )
    
    assert response.status_code == 204
    
    # Verify second interface still exists
    project_response = client.get(f"/api/projects/{project_id}")
    project = project_response.json()
    vm = project["vms"][0]
    assert len(vm["network_interfaces"]) == 1
    assert vm["network_interfaces"][0]["ip_address"] == "192.168.1.101"


def test_delete_network_interface_invalid_project_id():
    """Test deleting interface with invalid project ID format."""
    response = client.delete(
        "/api/projects/invalid-uuid/vms/test-vm/network-interfaces/interface-1"
    )
    
    assert response.status_code == 422  # FastAPI path validation
    error_data = response.json()
    assert "detail" in error_data


def test_delete_network_interface_idempotent():
    """Test that deleting the same interface twice is handled gracefully."""
    # Setup
    project_data = {"name": "idempotent-test", "description": ""}
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
    
    # Delete interface first time
    response1 = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}"
    )
    assert response1.status_code == 204
    
    # Delete interface second time
    response2 = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}"
    )
    assert response2.status_code == 404  # Should return not found


def test_delete_network_interface_response_headers():
    """Test that delete response has correct headers."""
    # Setup
    project_data = {"name": "headers-test", "description": ""}
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
    
    # Delete interface
    response = client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}"
    )
    
    assert response.status_code == 204
    # 204 responses should not have content-type header
    assert "content-type" not in response.headers or response.headers.get("content-type") == ""


def test_delete_network_interface_affects_project():
    """Test that deleting interface updates the project."""
    # Setup
    project_data = {"name": "project-update-test", "description": ""}
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
    
    # Verify interface exists
    project_response = client.get(f"/api/projects/{project_id}")
    project = project_response.json()
    vm = project["vms"][0]
    assert len(vm["network_interfaces"]) == 1
    
    # Delete interface
    client.delete(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/{interface_id}"
    )
    
    # Verify interface is gone
    project_response = client.get(f"/api/projects/{project_id}")
    project = project_response.json()
    vm = project["vms"][0]
    assert len(vm["network_interfaces"]) == 0


def test_delete_network_interface_http_method():
    """Test that only DELETE method is allowed."""
    # Setup
    project_data = {"name": "method-test", "description": ""}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Try GET method
    response = client.get(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/interface-1"
    )
    assert response.status_code == 405  # Method not allowed
    
    # Try POST method
    response = client.post(
        f"/api/projects/{project_id}/vms/test-vm/network-interfaces/interface-1",
        json={}
    )
    assert response.status_code == 405  # Method not allowed