"""
Project Plugin API endpoints for Vagrantfile Generator.

This module contains API endpoints for managing plugins within projects.
Plugins are referenced by ID in projects, maintaining consistency with
provisioners and triggers.
"""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends

from ..models.user_profile import UserProfile
from ..models.plugin import Plugin
from ..services import ProjectService, ProjectNotFoundError
from ..services.plugin_service import PluginService, PluginServiceError
from ..middleware.auth_middleware import get_optional_user

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> ProjectService:
    """Get ProjectService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return ProjectService(user_id=user_id)

# Dependency to get PluginService instance
def get_plugin_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> PluginService:
    """Get PluginService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return PluginService(user_id=user_id)


@router.get("/projects/{project_id}/plugins", response_model=List[Plugin])
async def get_project_plugins(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """
    Get all plugins for a project.
    Returns full Plugin objects by resolving the plugin IDs.
    """
    try:
        project = project_service.get_project(project_id)
        
        # Resolve plugin IDs to full Plugin objects
        plugins = []
        for plugin_id in project.global_plugins:
            try:
                plugin = plugin_service.get_plugin(plugin_id)
                if plugin:
                    plugins.append(plugin)
            except PluginServiceError:
                # Plugin not found - skip it (could be deleted)
                pass
        
        return plugins
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/plugins/{plugin_id}", response_model=Plugin, status_code=201)
async def add_plugin_to_project(
    project_id: UUID,
    plugin_id: str,
    project_service: ProjectService = Depends(get_project_service),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Add a plugin to a project by ID."""
    try:
        # Verify plugin exists
        plugin = plugin_service.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(status_code=404, detail=f"Plugin with ID {plugin_id} not found")
        
        # Add to project
        project_service.add_plugin_to_project(project_id, plugin_id)
        
        return plugin
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except PluginServiceError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/plugins/{plugin_id}", status_code=204)
async def remove_plugin_from_project(
    project_id: UUID,
    plugin_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Remove a plugin from a project."""
    try:
        project_service.remove_plugin_from_project(project_id, plugin_id)
        return None
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/projects/{project_id}/plugins/{plugin_id}/copy", response_model=dict)
async def copy_and_replace_plugin_in_project(
    project_id: UUID,
    plugin_id: str,
    project_service: ProjectService = Depends(get_project_service),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """
    Copy a shared plugin to user's library and update project to reference the copy.
    This enables seamless editing of shared plugins within a project context.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Get the shared plugin
        shared_plugin = plugin_service.get_plugin(plugin_id)
        if not shared_plugin:
            raise HTTPException(status_code=404, detail=f"Plugin {plugin_id} not found")
        
        if not shared_plugin.is_shared:
            raise HTTPException(status_code=400, detail="Plugin is already user-owned, no need to copy")
        
        # Copy the plugin to user's library
        copied_plugin = plugin_service.copy_shared_plugin(plugin_id)
        
        # Update project to reference the new copy
        project_service.update_plugin_in_project(project_id, plugin_id, copied_plugin.id)
        
        return {
            "old_id": plugin_id,
            "new_id": copied_plugin.id,
            "project_updated": True
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except PluginServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/plugins/{old_id}/replace/{new_id}", response_model=dict)
async def replace_plugin_in_project(
    project_id: UUID,
    old_id: str,
    new_id: str,
    project_service: ProjectService = Depends(get_project_service),
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """
    Replace a plugin reference in a project with a different plugin.
    Useful for reusing an existing user copy instead of creating a new one.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Verify the new plugin exists
        new_plugin = plugin_service.get_plugin(new_id)
        if not new_plugin:
            raise HTTPException(status_code=404, detail=f"Plugin '{new_id}' not found")
        
        # Update the project
        project_service.update_plugin_in_project(project_id, old_id, new_id)
        
        return {
            "old_id": old_id,
            "new_id": new_id,
            "project_updated": True
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
