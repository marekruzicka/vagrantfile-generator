"""
Project Plugin API endpoints for Vagrantfile GUI Generator.

This module contains API endpoints for managing plugins within projects.
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends

from ..models import PluginConfiguration, DeploymentStatus
from ..services import ProjectService, ProjectNotFoundError

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

@router.post("/projects/{project_id}/plugins", response_model=PluginConfiguration, status_code=201)
async def add_plugin_to_project(
    project_id: UUID,
    plugin_data: dict,
    project_service: ProjectService = Depends(get_project_service)
):
    """Add a plugin to a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot add plugin - project is locked in ready status")
        
        # Create plugin configuration
        plugin = PluginConfiguration(**plugin_data)
        
        # Add to project
        project = project_service.add_plugin_to_project(project_id, plugin)
        
        # Return the created plugin
        return plugin
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.get("/projects/{project_id}/plugins", response_model=List[PluginConfiguration])
async def get_project_plugins(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service)
):
    """Get all plugins for a project."""
    try:
        project = project_service.get_project(project_id)
        return project.global_plugins
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/projects/{project_id}/plugins/{plugin_name}", response_model=PluginConfiguration)
async def update_project_plugin(
    project_id: UUID,
    plugin_name: str,
    plugin_data: dict,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update a plugin in a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot modify plugin - project is locked in ready status")
        
        # Create plugin configuration
        plugin = PluginConfiguration(**plugin_data)
        
        # Update plugin in project
        project = project_service.update_plugin_in_project(project_id, plugin_name, plugin)
        
        # Find and return the updated plugin
        for p in project.global_plugins:
            if p.name == plugin_name:
                return p
        
        raise HTTPException(status_code=404, detail=f"Plugin '{plugin_name}' not found in project")
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/projects/{project_id}/plugins/{plugin_name}", status_code=204)
async def remove_plugin_from_project(
    project_id: UUID,
    plugin_name: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Remove a plugin from a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot remove plugin - project is locked in ready status")
        
        project_service.remove_plugin_from_project(project_id, plugin_name)
        return None
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
