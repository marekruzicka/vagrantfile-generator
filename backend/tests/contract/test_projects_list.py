"""
Contract test for GET /api/projects endpoint.

This test verifies the API contract specification for listing all projects.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app

client = TestClient(app)


def test_list_projects_empty():
    """Test listing projects when no projects exist."""
    # Note: This assumes a fresh start or cleaned database
    # In a real implementation, this might need database cleanup
    
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert "projects" in data
    assert isinstance(data["projects"], list)


def test_list_projects_with_data():
    """Test listing projects when projects exist."""
    # Arrange - Create some projects
    projects_to_create = [
        {"name": "project-alpha", "description": "First project"},
        {"name": "project-beta", "description": "Second project"},
        {"name": "project-gamma"}  # No description
    ]
    
    created_ids = []
    for project_data in projects_to_create:
        create_response = client.post("/api/projects", json=project_data)
        assert create_response.status_code == 201
        created_ids.append(create_response.json()["id"])
    
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert "projects" in data
    assert isinstance(data["projects"], list)
    assert len(data["projects"]) >= 3  # At least the ones we created
    
    # Check that our created projects are in the list
    project_names = [p["name"] for p in data["projects"]]
    assert "project-alpha" in project_names
    assert "project-beta" in project_names
    assert "project-gamma" in project_names


def test_list_projects_response_structure():
    """Test that each project in the list has the correct structure."""
    # Arrange - Create a project with known data
    create_data = {
        "name": "structure-test-project",
        "description": "Testing list response structure"
    }
    create_response = client.post("/api/projects", json=create_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Add VMs to the project to test vm_count
    project_data = create_response.json()
    project_data["vms"] = [
        {
            "name": "vm1",
            "box": "ubuntu/jammy64",
            "hostname": "vm1",
            "memory": 1024,
            "cpus": 1,
            "network_interfaces": [],
            "synced_folders": [],
            "provisioners": [],
            "plugins": []
        },
        {
            "name": "vm2",
            "box": "ubuntu/focal64",
            "hostname": "vm2",
            "memory": 2048,
            "cpus": 2,
            "network_interfaces": [],
            "synced_folders": [],
            "provisioners": [],
            "plugins": []
        }
    ]
    update_response = client.put(f"/api/projects/{project_id}", json=project_data)
    assert update_response.status_code == 200
    
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    project_list = data["projects"]
    
    # Find our test project
    test_project = None
    for project in project_list:
        if project["name"] == "structure-test-project":
            test_project = project
            break
    
    assert test_project is not None
    
    # Verify required fields in list view
    required_fields = ["id", "name", "description", "created_at", "updated_at", "vm_count"]
    for field in required_fields:
        assert field in test_project, f"Missing required field: {field}"
    
    # Verify field types
    assert isinstance(test_project["id"], str)
    assert isinstance(test_project["name"], str)
    assert isinstance(test_project["description"], str)
    assert isinstance(test_project["created_at"], str)
    assert isinstance(test_project["updated_at"], str)
    assert isinstance(test_project["vm_count"], int)
    
    # Verify values
    assert test_project["name"] == "structure-test-project"
    assert test_project["description"] == "Testing list response structure"
    assert test_project["vm_count"] == 2  # We added 2 VMs
    
    # Validate datetime format
    datetime.fromisoformat(test_project["created_at"].replace('Z', '+00:00'))
    datetime.fromisoformat(test_project["updated_at"].replace('Z', '+00:00'))


def test_list_projects_vm_count_accuracy():
    """Test that vm_count reflects the actual number of VMs."""
    # Arrange - Create projects with different VM counts
    test_cases = [
        {"name": "no-vms-project", "vm_count": 0},
        {"name": "one-vm-project", "vm_count": 1},
        {"name": "three-vms-project", "vm_count": 3}
    ]
    
    for case in test_cases:
        # Create project
        create_response = client.post("/api/projects", json={"name": case["name"]})
        project_id = create_response.json()["id"]
        
        # Add the specified number of VMs
        project_data = create_response.json()
        project_data["vms"] = []
        
        for i in range(case["vm_count"]):
            vm = {
                "name": f"vm{i+1}",
                "box": "ubuntu/jammy64",
                "hostname": f"vm{i+1}",
                "memory": 1024,
                "cpus": 1,
                "network_interfaces": [],
                "synced_folders": [],
                "provisioners": [],
                "plugins": []
            }
            project_data["vms"].append(vm)
        
        if case["vm_count"] > 0:
            update_response = client.put(f"/api/projects/{project_id}", json=project_data)
            assert update_response.status_code == 200
    
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    project_list = data["projects"]
    
    # Verify VM counts
    for case in test_cases:
        project = next((p for p in project_list if p["name"] == case["name"]), None)
        assert project is not None
        assert project["vm_count"] == case["vm_count"]


def test_list_projects_ordering():
    """Test project list ordering (should be consistent)."""
    # Arrange - Create projects with known names
    project_names = ["zebra-project", "alpha-project", "beta-project"]
    
    for name in project_names:
        create_response = client.post("/api/projects", json={"name": name})
        assert create_response.status_code == 201
    
    # Act - Get list multiple times
    response1 = client.get("/api/projects")
    response2 = client.get("/api/projects")
    
    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    projects1 = response1.json()["projects"]
    projects2 = response2.json()["projects"]
    
    # Order should be consistent between calls
    names1 = [p["name"] for p in projects1]
    names2 = [p["name"] for p in projects2]
    assert names1 == names2


def test_list_projects_content_type():
    """Test that the response has correct content type."""
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    assert "application/json" in response.headers.get("content-type", "")


def test_list_projects_http_methods():
    """Test that only GET method is allowed."""
    # Test other HTTP methods should not work
    wrong_methods = [
        lambda: client.post("/api/projects", json={"name": "test"}),  # This is for creating, different endpoint
        lambda: client.put("/api/projects"),
        lambda: client.delete("/api/projects")
    ]
    
    # PUT and DELETE should not be allowed on the list endpoint
    response = client.put("/api/projects")
    assert response.status_code in [404, 405]  # Method not allowed or not found
    
    response = client.delete("/api/projects")  
    assert response.status_code in [404, 405]  # Method not allowed or not found


def test_list_projects_no_sensitive_data():
    """Test that the list view doesn't expose sensitive or detailed data."""
    # Arrange - Create a project with detailed configuration
    create_data = {"name": "detailed-project", "description": "Has detailed config"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Add detailed VM configuration
    project_data = create_response.json()
    project_data["vms"] = [
        {
            "name": "detailed-vm",
            "box": "ubuntu/jammy64",
            "hostname": "detailed",
            "memory": 4096,
            "cpus": 4,
            "network_interfaces": [
                {
                    "type": "private_network",
                    "ip": "192.168.1.100",
                    "netmask": "255.255.255.0"
                }
            ],
            "synced_folders": [],
            "provisioners": [],
            "plugins": []
        }
    ]
    update_response = client.put(f"/api/projects/{project_id}", json=project_data)
    assert update_response.status_code == 200
    
    # Act
    response = client.get("/api/projects")
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    detailed_project = next(
        (p for p in data["projects"] if p["name"] == "detailed-project"), 
        None
    )
    assert detailed_project is not None
    
    # List view should NOT include detailed VM configurations
    assert "vms" not in detailed_project
    assert "global_plugins" not in detailed_project
    assert "version" not in detailed_project
    
    # Should only have summary information
    expected_fields = {"id", "name", "description", "created_at", "updated_at", "vm_count"}
    actual_fields = set(detailed_project.keys())
    assert actual_fields == expected_fields