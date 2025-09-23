"""
Contract test for POST /api/projects endpoint.

This test verifies the API contract specification for creating a new project.
MUST FAIL until the actual implementation is created.
"""

import pytest
from fastapi.testclient import TestClient
from datetime import datetime
import uuid

from src.main import app

client = TestClient(app)


def test_create_project_success():
    """Test successful project creation."""
    # Arrange
    request_data = {
        "name": "test-project",
        "description": "A test project"
    }
    
    # Act
    response = client.post("/api/projects", json=request_data)
    
    # Assert
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert uuid.UUID(data["id"])  # Validates UUID format
    assert data["name"] == "test-project"
    assert data["description"] == "A test project"
    assert data["version"] == "1.0.0"
    assert "created_at" in data
    assert "updated_at" in data
    assert data["vms"] == []
    assert data["global_plugins"] == []
    
    # Validate datetime format
    datetime.fromisoformat(data["created_at"].replace('Z', '+00:00'))
    datetime.fromisoformat(data["updated_at"].replace('Z', '+00:00'))


def test_create_project_minimal_data():
    """Test project creation with minimal required data."""
    # Arrange
    request_data = {
        "name": "minimal-project"
    }
    
    # Act
    response = client.post("/api/projects", json=request_data)
    
    # Assert
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "minimal-project"
    assert data["description"] == ""  # Default empty description


def test_create_project_invalid_name():
    """Test project creation with invalid name."""
    # Arrange
    test_cases = [
        {"name": ""},  # Empty name
        {"name": None},  # Null name
        {"name": "a" * 256},  # Too long name
        {"name": "invalid/name"},  # Invalid characters
        {}  # Missing name
    ]
    
    for request_data in test_cases:
        # Act
        response = client.post("/api/projects", json=request_data)
        
        # Assert
        assert response.status_code == 400
        assert "error" in response.json()


def test_create_project_duplicate_name():
    """Test project creation with duplicate name."""
    # Arrange
    request_data = {
        "name": "duplicate-project",
        "description": "First project"
    }
    
    # Create first project
    response1 = client.post("/api/projects", json=request_data)
    assert response1.status_code == 201
    
    # Act - Try to create duplicate
    response2 = client.post("/api/projects", json=request_data)
    
    # Assert
    assert response2.status_code == 409
    error_data = response2.json()
    assert "error" in error_data
    assert "already exists" in error_data["error"].lower()


def test_create_project_invalid_json():
    """Test project creation with invalid JSON."""
    # Act
    response = client.post(
        "/api/projects", 
        data="invalid json",
        headers={"Content-Type": "application/json"}
    )
    
    # Assert
    assert response.status_code == 422  # FastAPI validation error


def test_create_project_extra_fields():
    """Test project creation ignores extra fields."""
    # Arrange
    request_data = {
        "name": "extra-fields-project",
        "description": "Test project",
        "extra_field": "should be ignored",
        "version": "2.0.0"  # Should be ignored, always 1.0.0 for new projects
    }
    
    # Act
    response = client.post("/api/projects", json=request_data)
    
    # Assert
    assert response.status_code == 201
    
    data = response.json()
    assert data["name"] == "extra-fields-project"
    assert data["version"] == "1.0.0"  # Not 2.0.0
    assert "extra_field" not in data