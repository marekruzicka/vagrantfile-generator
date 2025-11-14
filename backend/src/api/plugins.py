"""
Plugin management API endpoints for Vagrantfile Generator.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from ..models.user_profile import UserProfile
from ..models.plugin import Plugin, PluginCreate, PluginUpdate, PluginSummary
from ..services.plugin_service import PluginService, PluginServiceError
from ..middleware.auth_middleware import get_optional_user

router = APIRouter()

# Dependency to get PluginService instance
def get_plugin_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> PluginService:
    """Get PluginService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return PluginService(user_id=user_id)


@router.get("/plugins", response_model=List[PluginSummary])
async def list_plugins(plugin_service: PluginService = Depends(get_plugin_service)):
    """Get list of all plugins."""
    try:
        plugins = plugin_service.list_plugins()
        return plugins
    except PluginServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/plugins/{plugin_id}", response_model=Plugin)
async def get_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Get a specific plugin by ID."""
    try:
        plugin = plugin_service.get_plugin(plugin_id)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        return plugin
    except PluginServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/plugins", response_model=Plugin, status_code=status.HTTP_201_CREATED)
async def create_plugin(
    plugin_data: PluginCreate,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Create a new plugin."""
    try:
        plugin = plugin_service.create_plugin(plugin_data)
        return plugin
    except PluginServiceError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/plugins/{plugin_id}", response_model=Plugin)
async def update_plugin(
    plugin_id: str,
    plugin_data: PluginUpdate,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Update an existing plugin."""
    try:
        # Check if plugin is shared (read-only)
        if plugin_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_path = file_service.get_shared_data_path("plugins") / f"{plugin_id}.json"
            if shared_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify shared resource - shared resources are read-only"
                )
        
        plugin = plugin_service.update_plugin(plugin_id, plugin_data)
        if not plugin:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        return plugin
    except PluginServiceError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/plugins/{plugin_id}")
async def delete_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """Delete a plugin."""
    try:
        # Check if plugin is shared (read-only)
        if plugin_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_path = file_service.get_shared_data_path("plugins") / f"{plugin_id}.json"
            if shared_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete shared resource - shared resources are read-only"
                )
        
        deleted = plugin_service.delete_plugin(plugin_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin with ID {plugin_id} not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Plugin {plugin_id} deleted successfully"}
        )
    except PluginServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/plugins/{plugin_id}/copy", response_model=Plugin)
async def copy_shared_plugin(
    plugin_id: str,
    plugin_service: PluginService = Depends(get_plugin_service)
):
    """
    Copy a shared plugin to user's directory.
    User can then edit/customize their copy.
    """
    try:
        copied_plugin = plugin_service.copy_shared_plugin(plugin_id)
        return copied_plugin
    except PluginServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
