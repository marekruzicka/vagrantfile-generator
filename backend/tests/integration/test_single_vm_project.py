"""
Integration test for single VM project creation.

This test verifies the complete user scenario from the quickstart guide.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import json

from src.main import app

client = TestClient(app)


def test_single_vm_project_creation():
    """Test complete single VM project creation scenario."""
    
    # Step 1-3: Create new project
    project_data = {
        "name": "my-vagrant-project",
        "description": "Test project for single VM"
    }
    
    create_response = client.post("/api/projects", json=project_data)
    assert create_response.status_code == 201
    
    project = create_response.json()
    project_id = project["id"]
    assert project["name"] == "my-vagrant-project"
    assert project["vms"] == []
    
    # Step 4-5: Add Virtual Machine
    vm_data = {
        "name": "web-server",
        "box": "ubuntu/jammy64",
        "hostname": "web-server",
        "memory": 2048,
        "cpus": 2
    }
    
    vm_response = client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    assert vm_response.status_code == 201
    
    vm = vm_response.json()
    assert vm["name"] == "web-server"
    assert vm["box"] == "ubuntu/jammy64"
    assert vm["memory"] == 2048
    assert vm["cpus"] == 2
    
    # Step 6: Add private network interface
    network_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.33.10",
        "netmask": "255.255.255.0"
    }
    
    network_response = client.post(
        f"/api/projects/{project_id}/vms/web-server/network-interfaces",
        json=network_data
    )
    assert network_response.status_code == 201
    
    # Step 7: Generate Vagrantfile
    generate_response = client.post(f"/api/projects/{project_id}/generate")
    assert generate_response.status_code == 200
    
    generated = generate_response.json()
    assert generated["filename"] == "Vagrantfile"
    assert generated["validation"]["is_valid"] == True
    assert len(generated["validation"]["errors"]) == 0
    
    # Verify generated content contains expected configuration
    content = generated["content"]
    assert "web-server" in content
    assert "ubuntu/jammy64" in content
    assert "192.168.33.10" in content
    assert "2048" in content
    
    # Step 8: Verify project state
    final_project = client.get(f"/api/projects/{project_id}")
    assert final_project.status_code == 200
    
    final_data = final_project.json()
    assert len(final_data["vms"]) == 1
    assert len(final_data["vms"][0]["network_interfaces"]) == 1
    
    network_interface = final_data["vms"][0]["network_interfaces"][0]
    assert network_interface["ip_address"] == "192.168.33.10"
    assert network_interface["type"] == "private_network"
    
    # Step 9: Project persistence (already saved automatically)
    # Verify we can retrieve the project again
    retrieve_response = client.get(f"/api/projects/{project_id}")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["name"] == "my-vagrant-project"


def test_single_vm_project_validation():
    """Test that the single VM project passes validation."""
    
    # Create the same project as above
    project_data = {"name": "validation-test-project"}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    # Add VM
    vm_data = {
        "name": "web-server",
        "box": "ubuntu/jammy64",
        "memory": 2048,
        "cpus": 2
    }
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Add network interface
    network_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.33.10"
    }
    client.post(f"/api/projects/{project_id}/vms/web-server/network-interfaces", json=network_data)
    
    # Test validation endpoint
    validate_response = client.post(f"/api/projects/{project_id}/validate")
    assert validate_response.status_code == 200
    
    validation = validate_response.json()
    assert validation["is_valid"] == True
    assert validation["vm_count"] == 1
    assert validation["network_interfaces_count"] == 1
    assert len(validation["errors"]) == 0


def test_single_vm_project_appears_in_list():
    """Test that created project appears in projects list."""
    
    # Create project
    project_data = {"name": "list-test-project"}
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    # Add VM to increase vm_count
    vm_data = {"name": "test-vm", "box": "ubuntu/jammy64"}
    client.post(f"/api/projects/{project_id}/vms", json=vm_data)
    
    # Check project list
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    
    projects = list_response.json()["projects"]
    test_project = next(
        (p for p in projects if p["name"] == "list-test-project"), 
        None
    )
    
    assert test_project is not None
    assert test_project["vm_count"] == 1
    assert "created_at" in test_project
    assert "updated_at" in test_project