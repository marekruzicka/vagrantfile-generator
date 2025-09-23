"""
Contract test for DELETE /api/projects/{project_id} endpoint.

This test verifies the API contract specification for deleting a project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
import uuid

from src.main import app

client = TestClient(app)


def test_delete_project_success():
    """Test successful project deletion."""
    # Arrange - Create a project first
    create_data = {
        "name": "project-to-delete",
        "description": "This project will be deleted"
    }
    create_response = client.post("/api/projects", json=create_data)
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]
    
    # Verify project exists
    get_response = client.get(f"/api/projects/{project_id}")
    assert get_response.status_code == 200
    
    # Act
    response = client.delete(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 204
    assert response.content == b""  # No content in 204 response
    
    # Verify project is actually deleted
    verify_response = client.get(f"/api/projects/{project_id}")
    assert verify_response.status_code == 404


def test_delete_project_not_found():
    """Test deleting non-existent project."""
    # Arrange
    fake_id = str(uuid.uuid4())
    
    # Act
    response = client.delete(f"/api/projects/{fake_id}")
    
    # Assert
    assert response.status_code == 404
    error_data = response.json()
    assert "error" in error_data


def test_delete_project_invalid_uuid():
    """Test deleting project with invalid UUID."""
    # Arrange
    invalid_ids = [
        "not-a-uuid",
        "123",
        "",
        "invalid-uuid-format",
        "12345678-1234-1234-1234-123456789abc-extra"
    ]
    
    for invalid_id in invalid_ids:
        # Act
        response = client.delete(f"/api/projects/{invalid_id}")
        
        # Assert
        # Should be 422 (validation error) or 404 depending on FastAPI path validation
        assert response.status_code in [404, 422]


def test_delete_project_idempotent():
    """Test that deleting the same project twice is idempotent."""
    # Arrange - Create a project
    create_data = {"name": "idempotent-delete-test"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act - Delete project first time
    response1 = client.delete(f"/api/projects/{project_id}")
    assert response1.status_code == 204
    
    # Act - Delete same project again
    response2 = client.delete(f"/api/projects/{project_id}")
    
    # Assert - Should return 404 (not found) for second deletion
    assert response2.status_code == 404


def test_delete_project_with_vms():
    """Test deleting project that contains VMs."""
    # Arrange - Create a project and add VMs to it
    create_data = {"name": "project-with-vms"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Add VMs to the project (using PUT to update)
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
    
    # Act - Delete the project
    response = client.delete(f"/api/projects/{project_id}")
    
    # Assert - Should successfully delete project with all its VMs
    assert response.status_code == 204
    
    # Verify project and all VMs are gone
    verify_response = client.get(f"/api/projects/{project_id}")
    assert verify_response.status_code == 404


def test_delete_project_response_headers():
    """Test that DELETE response has correct headers."""
    # Arrange
    create_data = {"name": "header-test-project"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Act
    response = client.delete(f"/api/projects/{project_id}")
    
    # Assert
    assert response.status_code == 204
    
    # 204 No Content should not have Content-Type header
    assert "content-type" not in response.headers or response.headers.get("content-type") == ""
    assert len(response.content) == 0


def test_delete_project_affects_project_list():
    """Test that deleting a project removes it from the project list."""
    # Arrange - Create multiple projects
    projects_to_create = ["project-1", "project-2", "project-3"]
    created_ids = []
    
    for project_name in projects_to_create:
        create_response = client.post("/api/projects", json={"name": project_name})
        assert create_response.status_code == 201
        created_ids.append(create_response.json()["id"])
    
    # Verify all projects exist in list
    list_response = client.get("/api/projects")
    assert list_response.status_code == 200
    project_names = [p["name"] for p in list_response.json()["projects"]]
    assert all(name in project_names for name in projects_to_create)
    
    # Act - Delete one project
    project_to_delete = created_ids[1]  # Delete "project-2"
    delete_response = client.delete(f"/api/projects/{project_to_delete}")
    assert delete_response.status_code == 204
    
    # Assert - Verify it's removed from the list
    updated_list_response = client.get("/api/projects")
    assert updated_list_response.status_code == 200
    updated_project_names = [p["name"] for p in updated_list_response.json()["projects"]]
    
    assert "project-1" in updated_project_names
    assert "project-2" not in updated_project_names  # Should be deleted
    assert "project-3" in updated_project_names


def test_delete_project_http_method():
    """Test that only DELETE method is allowed for deletion."""
    # Arrange
    create_data = {"name": "method-test-project"}
    create_response = client.post("/api/projects", json=create_data)
    project_id = create_response.json()["id"]
    
    # Test other HTTP methods should not work for deletion
    wrong_methods = [
        lambda: client.get(f"/api/projects/{project_id}/delete"),
        lambda: client.post(f"/api/projects/{project_id}/delete"),
        lambda: client.put(f"/api/projects/{project_id}/delete")
    ]
    
    for method_call in wrong_methods:
        response = method_call()
        # Should return 404 (not found) or 405 (method not allowed)
        assert response.status_code in [404, 405]
    
    # Verify project still exists after wrong method attempts
    verify_response = client.get(f"/api/projects/{project_id}")
    assert verify_response.status_code == 200