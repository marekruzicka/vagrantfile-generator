"""
Project API endpoints for Vagrantfile GUI Generator.

This module contains all API endpoints related to project management.
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models import Project, ProjectCreate, ProjectUpdate, ProjectSummary
from ..services import ProjectService, ProjectNotFoundError

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

@router.post("/projects", response_model=Project, status_code=201)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service)
):
    """Create a new project."""
    try:
        project = project_service.create_project(project_data)
        return project
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get a specific project by ID."""
    try:
        project = project_service.get_project(project_id)
        return project
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update an existing project."""
    try:
        project = project_service.update_project(project_id, project_data)
        return project
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/projects/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service)
):
    """Delete a project."""
    success = project_service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    
    return None  # 204 No Content

@router.get("/projects", response_model=dict)
async def list_projects(
    project_service: ProjectService = Depends(get_project_service)
):
    """List all projects."""
    projects = project_service.list_projects()
    return {"projects": projects}

@router.post("/projects/{project_id}/validate", response_model=dict)
async def validate_project(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service)
):
    """Validate a project configuration."""
    try:
        validation_result = project_service.validate_project(project_id)
        return validation_result
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))