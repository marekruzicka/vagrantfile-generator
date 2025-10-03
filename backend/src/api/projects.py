"""
Project API endpoints for Vagrantfile Generator.

This module contains all API endpoints related to project management.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from ..models import Project, ProjectCreate, ProjectUpdate, ProjectSummary, DeploymentStatus
from ..services import ProjectService, ProjectNotFoundError
from ..services.plugin_service import PluginService

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

# Dependency to get PluginService instance
def get_plugin_service() -> PluginService:
    """Get PluginService instance."""
    return PluginService()

@router.get("/projects/stats", response_model=dict)
async def get_project_stats(
    project_service: ProjectService = Depends(get_project_service)
):
    """Get project statistics including counts by deployment status."""
    all_projects = project_service.list_projects()
    
    stats = {
        "total_projects": len(all_projects),
        "total_vms": sum(p.vm_count for p in all_projects),
        "ready": len([p for p in all_projects if p.deployment_status == DeploymentStatus.READY]),
        "draft": len([p for p in all_projects if p.deployment_status == DeploymentStatus.DRAFT])
    }
    
    return stats

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
    project_service: ProjectService = Depends(get_project_service),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Get a specific project by ID."""
    try:
        project = project_service.get_project(project_id)
        
        # Enrich plugins with deprecation status from master plugins list
        for plugin_config in project.global_plugins:
            try:
                master_plugin = plugin_service.get_plugin_by_name(plugin_config.name)
                if master_plugin:
                    plugin_config.is_deprecated = master_plugin.is_deprecated
            except:
                pass
        
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
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot modify project - project is locked in ready status")
        
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

@router.patch("/projects/{project_id}/deployment-status")
async def update_deployment_status(
    project_id: UUID,
    status: DeploymentStatus,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update project deployment status."""
    try:
        project = project_service.update_deployment_status(project_id, status)
        return {"id": project.id, "deployment_status": project.deployment_status}
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/projects", response_model=dict)
async def list_projects(
    status: Optional[DeploymentStatus] = None,
    project_service: ProjectService = Depends(get_project_service)
):
    """List all projects, optionally filtered by deployment status."""
    if status:
        projects = project_service.list_projects_by_status(status)
    else:
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