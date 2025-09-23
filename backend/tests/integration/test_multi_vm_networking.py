"""
Integration test for multi-VM project with networking.

This test validates end-to-end functionality for complex scenarios.
"""

import pytest
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


def test_multi_vm_networking_scenario():
    """Test creating a multi-VM project with complex networking."""
    # Create a project
    project_data = {
        "name": "multi-vm-network-test",
        "description": "Test project with multiple VMs and networking"
    }
    
    create_response = client.post("/api/projects", json=project_data)
    assert create_response.status_code == 201
    project = create_response.json()
    project_id = project["id"]
    
    # Add web server VM
    web_vm_data = {
        "name": "web-server",
        "box": "ubuntu/jammy64",
        "memory": 2048,
        "cpus": 2,
        "hostname": "web.local"
    }
    
    web_response = client.post(f"/api/projects/{project_id}/vms", json=web_vm_data)
    assert web_response.status_code == 201
    
    # Add database VM
    db_vm_data = {
        "name": "database",
        "box": "ubuntu/jammy64", 
        "memory": 1024,
        "cpus": 1,
        "hostname": "db.local"
    }
    
    db_response = client.post(f"/api/projects/{project_id}/vms", json=db_vm_data)
    assert db_response.status_code == 201
    
    # Add load balancer VM
    lb_vm_data = {
        "name": "load-balancer",
        "box": "ubuntu/jammy64",
        "memory": 512,
        "cpus": 1,
        "hostname": "lb.local"
    }
    
    lb_response = client.post(f"/api/projects/{project_id}/vms", json=lb_vm_data)
    assert lb_response.status_code == 201
    
    # Add private network interfaces
    # Web server private network
    web_private_interface = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.10.10",
        "netmask": "255.255.255.0"
    }
    
    web_interface_response = client.post(
        f"/api/projects/{project_id}/vms/web-server/network-interfaces",
        json=web_private_interface
    )
    assert web_interface_response.status_code == 201
    
    # Database private network
    db_private_interface = {
        "type": "private_network", 
        "ip_assignment": "static",
        "ip_address": "192.168.10.20",
        "netmask": "255.255.255.0"
    }
    
    db_interface_response = client.post(
        f"/api/projects/{project_id}/vms/database/network-interfaces",
        json=db_private_interface
    )
    assert db_interface_response.status_code == 201
    
    # Load balancer private network
    lb_private_interface = {
        "type": "private_network",
        "ip_assignment": "static", 
        "ip_address": "192.168.10.30",
        "netmask": "255.255.255.0"
    }
    
    lb_interface_response = client.post(
        f"/api/projects/{project_id}/vms/load-balancer/network-interfaces",
        json=lb_private_interface
    )
    assert lb_interface_response.status_code == 201
    
    # Add port forwarding for web access
    web_port_forward = {
        "type": "forwarded_port",
        "guest_port": 80,
        "host_port": 8080,
        "protocol": "tcp"
    }
    
    port_forward_response = client.post(
        f"/api/projects/{project_id}/vms/load-balancer/network-interfaces",
        json=web_port_forward
    )
    assert port_forward_response.status_code == 201
    
    # Verify project structure
    project_response = client.get(f"/api/projects/{project_id}")
    assert project_response.status_code == 200
    
    project = project_response.json()
    assert len(project["vms"]) == 3
    
    # Check each VM has expected configuration
    vms_by_name = {vm["name"]: vm for vm in project["vms"]}
    
    # Web server checks
    web_vm = vms_by_name["web-server"]
    assert web_vm["memory"] == 2048
    assert web_vm["cpus"] == 2
    assert web_vm["hostname"] == "web.local"
    assert len(web_vm["network_interfaces"]) == 1
    assert web_vm["network_interfaces"][0]["ip_address"] == "192.168.10.10"
    
    # Database checks
    db_vm = vms_by_name["database"]
    assert db_vm["memory"] == 1024
    assert db_vm["cpus"] == 1
    assert db_vm["hostname"] == "db.local"
    assert len(db_vm["network_interfaces"]) == 1
    assert db_vm["network_interfaces"][0]["ip_address"] == "192.168.10.20"
    
    # Load balancer checks  
    lb_vm = vms_by_name["load-balancer"]
    assert lb_vm["memory"] == 512
    assert lb_vm["cpus"] == 1
    assert lb_vm["hostname"] == "lb.local"
    assert len(lb_vm["network_interfaces"]) == 2  # Private network + port forward
    
    # Check for private network interface
    private_interfaces = [intf for intf in lb_vm["network_interfaces"] if intf["type"] == "private_network"]
    assert len(private_interfaces) == 1
    assert private_interfaces[0]["ip_address"] == "192.168.10.30"
    
    # Check for port forwarding interface
    port_interfaces = [intf for intf in lb_vm["network_interfaces"] if intf["type"] == "forwarded_port"]
    assert len(port_interfaces) == 1
    assert port_interfaces[0]["guest_port"] == 80
    assert port_interfaces[0]["host_port"] == 8080
    
    # Generate Vagrantfile and verify it contains all VMs
    generation_response = client.post(f"/api/projects/{project_id}/generate")
    assert generation_response.status_code == 200
    
    result = generation_response.json()
    vagrantfile_content = result["content"]
    
    # Check that all VM names appear in the generated Vagrantfile
    assert "web-server" in vagrantfile_content
    assert "database" in vagrantfile_content  
    assert "load-balancer" in vagrantfile_content
    
    # Check that network configurations are included
    assert "192.168.10.10" in vagrantfile_content
    assert "192.168.10.20" in vagrantfile_content
    assert "192.168.10.30" in vagrantfile_content
    assert "forwarded_port" in vagrantfile_content or "8080" in vagrantfile_content
    
    # Verify project appears in project list
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    
    projects_list = list_response.json()
    project_names = [p["name"] for p in projects_list["projects"]]
    assert "multi-vm-network-test" in project_names
    
    # Find our project in the list and verify VM count
    our_project = next(p for p in projects_list["projects"] if p["name"] == "multi-vm-network-test")
    assert our_project["vm_count"] == 3


def test_networking_validation_scenario():
    """Test network validation with conflicting IPs."""
    # Create project
    project_data = {
        "name": "network-validation-test",
        "description": "Test network validation"
    }
    
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    # Add two VMs
    vm1_data = {"name": "vm1", "box": "ubuntu/jammy64"}
    vm2_data = {"name": "vm2", "box": "ubuntu/jammy64"}
    
    client.post(f"/api/projects/{project_id}/vms", json=vm1_data)
    client.post(f"/api/projects/{project_id}/vms", json=vm2_data)
    
    # Add network interface to first VM
    interface1_data = {
        "type": "private_network",
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"
    }
    
    response1 = client.post(
        f"/api/projects/{project_id}/vms/vm1/network-interfaces",
        json=interface1_data
    )
    assert response1.status_code == 201
    
    # Try to add conflicting IP to second VM
    interface2_data = {
        "type": "private_network", 
        "ip_assignment": "static",
        "ip_address": "192.168.1.100"  # Same IP - should work at API level but validation should catch it
    }
    
    response2 = client.post(
        f"/api/projects/{project_id}/vms/vm2/network-interfaces", 
        json=interface2_data
    )
    assert response2.status_code == 201  # API allows it, validation service should catch conflicts
    
    # If we had a validation endpoint, we could test it here
    # For now, this test documents the expected behavior


def test_resource_intensive_scenario():
    """Test scenario with high resource allocation."""
    # Create project
    project_data = {
        "name": "resource-intensive-test",
        "description": "Test high resource allocation"
    }
    
    create_response = client.post("/api/projects", json=project_data)
    project_id = create_response.json()["id"]
    
    # Add VM with high resource allocation
    high_resource_vm = {
        "name": "high-resource-vm",
        "box": "ubuntu/jammy64",
        "memory": 8192,  # 8GB
        "cpus": 4
    }
    
    vm_response = client.post(f"/api/projects/{project_id}/vms", json=high_resource_vm)
    assert vm_response.status_code == 201
    
    # Add another VM to push total resources higher
    another_vm = {
        "name": "another-vm",
        "box": "ubuntu/jammy64", 
        "memory": 4096,  # 4GB
        "cpus": 2
    }
    
    vm2_response = client.post(f"/api/projects/{project_id}/vms", json=another_vm)
    assert vm2_response.status_code == 201
    
    # Verify project was created with high resource VMs
    project_response = client.get(f"/api/projects/{project_id}")
    project = project_response.json()
    
    total_memory = sum(vm["memory"] for vm in project["vms"])
    total_cpus = sum(vm["cpus"] for vm in project["vms"])
    
    assert total_memory == 12288  # 12GB total
    assert total_cpus == 6
    
    # Generate Vagrantfile to ensure it handles high resource allocation
    generation_response = client.post(f"/api/projects/{project_id}/generate")
    assert generation_response.status_code == 200
    
    result = generation_response.json()
    vagrantfile_content = result["content"]
    
    # Check that memory and CPU settings are in the Vagrantfile
    assert "8192" in vagrantfile_content  # High memory setting
    assert "4096" in vagrantfile_content  # Second VM memory
    assert "cpus" in vagrantfile_content.lower() or "cpu" in vagrantfile_content.lower()