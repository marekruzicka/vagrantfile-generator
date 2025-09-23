"""
Contract test for PUT /api/projects/{project_id} endpoint.

This test verifies the API contract specification for updating a project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from src.main import app

client = TestClient(app)


def test_update_project_success():
    """Test successful project update."""
    # Arrange - Create a project first
    create_data = {
        "name": "original-project",
        "description": "Original description"
    }
    create_response = client.post("/api/projects", json=create_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    original_created_at = create_response.json()["created_at"]
    
    # Get the current project state to modify it
    get_response = client.get(f"/api/projects/{project_id}")
    project_data = get_response.json()
    
    # Modify the project data
    project_data["name"] = "updated-project"
    project_data["description"] = "Updated description"
    
    # Act
    response = client.put(f"/api/projects/{project_id}", json=project_data)
    
    # Assert
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "updated-project"
    assert data["description"] == "Updated description"
    assert data["version"] == "1.0.0"
    assert data["created_at"] == original_created_at  # Should not change
    assert data["updated_at"] != original_created_at  # Should be updated
    
    # Validate datetime format
    datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))


def test_update_project_partial_data():
    """Test updating project with partial data."""
    # Arrange
    create_data = {"name": "partial-test", "description": "Original"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act - Update only the description
    update_data = {
        "name": "partial-test",  # Keep same name
        "description": "Updated description only",
        "version": "1.0.0",
        "vms": [],
        "global_plugins": []
    }
    response = client.put(f"/api/projects/{project_id}", json=update_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "partial-test"
    assert data["description"] == "Updated description only"


def test_update_project_with_vms():
    """Test updating project with VM configurations."""
    # Arrange
    create_data = {"name": "vm-test-project"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act - Update with VM data
    update_data = {
        "name": "vm-test-project",
        "description": "",
        "version": "1.0.0",
        "vms": [
            {
                "name": "web-server",
                "box": "ubuntu/jammy64",
                "hostname": "web",
                "memory": 2048,
                "cpus": 2,
                "network_interfaces": [],
                "synced_folders": [],
                "provisioners": [],
                "plugins": []
            }
        ],
        "global_plugins": []
    }
    response = client.put(f"/api/projects/{project_id}", json=update_data)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert len(data["vms"]) == 1
    vm = data["vms"][0]
    assert vm["name"] == "web-server"
    assert vm["box"] == "ubuntu/jammy64"
    assert vm["memory"] == 2048
    assert vm["cpus"] == 2


def test_update_project_not_found():
    """Test updating non-existent project."""
    # Arrange
    fake_id = str(uuid.uuid4())
    update_data = {
        "name": "non-existent",
        "description": "Should not work",
        "version": "1.0.0",
        "vms": [],
        "global_plugins": []
    }
    
    # Act
    response = client.put(f"/api/projects/{fake_id}", json=update_data)
    
    # Assert
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data


def test_update_project_invalid_data():
    """Test updating project with invalid data."""
    # Arrange - Create a project first
    create_data = {"name": "validation-test"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Test cases with invalid data
    invalid_updates = [
        {"name": ""},  # Empty name
        {"name": None},  # Null name
        {"name": "a" * 256},  # Too long name
        {"vms": "not-a-list"},  # Invalid VMs format
        {"global_plugins": "not-a-list"},  # Invalid plugins format
        {"version": None},  # Invalid version
        {}  # Missing required fields
    ]
    
    for update_data in invalid_updates:
        # Act
        response = client.put(f"/api/projects/{project_id}", json=update_data)
        
        # Assert
        assert response.status_code == 400


def test_update_project_invalid_vm_data():
    """Test updating project with invalid VM data."""
    # Arrange
    create_data = {"name": "invalid-vm-test"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Invalid VM configurations
    invalid_vm_data = {
        "name": "invalid-vm-test",
        "description": "",
        "version": "1.0.0",
        "vms": [
            {
                "name": "",  # Empty VM name
                "box": "ubuntu/jammy64",
                "memory": "not-a-number",  # Invalid memory
                "cpus": -1  # Invalid CPU count
            }
        ],
        "global_plugins": []
    }
    
    # Act
    response = client.put(f"/api/projects/{project_id}", json=invalid_vm_data)
    
    # Assert
    assert response.status_code == 400


def test_update_project_duplicate_vm_names():
    """Test updating project with duplicate VM names."""
    # Arrange
    create_data = {"name": "duplicate-vm-test"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Duplicate VM names
    duplicate_vm_data = {
        "name": "duplicate-vm-test",
        "description": "",
        "version": "1.0.0",
        "vms": [
            {
                "name": "same-name",
                "box": "ubuntu/jammy64",
                "memory": 1024,
                "cpus": 1,
                "network_interfaces": [],
                "synced_folders": [],
                "provisioners": [],
                "plugins": []
            },
            {
                "name": "same-name",  # Duplicate name
                "box": "ubuntu/focal64",
                "memory": 2048,
                "cpus": 2,
                "network_interfaces": [],
                "synced_folders": [],
                "provisioners": [],
                "plugins": []
            }
        ],
        "global_plugins": []
    }
    
    # Act
    response = client.put(f"/api/projects/{project_id}", json=duplicate_vm_data)
    
    # Assert
    assert response.status_code == 400
    error_data = response.json()
    assert "duplicate" in error_data["error"].lower() or "unique" in error_data["error"].lower()


def test_update_project_invalid_uuid():
    """Test updating project with invalid UUID."""
    # Arrange
    update_data = {
        "name": "test",
        "description": "",
        "version": "1.0.0",
        "vms": [],
        "global_plugins": []
    }
    
    invalid_ids = ["not-a-uuid", "123", ""]
    
    for invalid_id in invalid_ids:
        # Act
        response = client.put(f"/api/projects/{invalid_id}", json=update_data)
        
        # Assert
        assert response.status_code in [404, 422]  # Depends on FastAPI path validation