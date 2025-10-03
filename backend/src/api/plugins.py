"""
Plugin management API endpoints for Vagrantfile Generator.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.plugin import Plugin, PluginCreate, PluginUpdate, PluginSummary
from ..services.plugin_service import PluginService, PluginServiceError

router = APIRouter()
plugin_service = PluginService()


@router.get("/plugins", response_model=List[PluginSummary])
async def list_plugins():
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
async def get_plugin(plugin_id: str):
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
async def create_plugin(plugin_data: PluginCreate):
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
async def update_plugin(plugin_id: str, plugin_data: PluginUpdate):
    """Update an existing plugin."""
    try:
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
async def delete_plugin(plugin_id: str):
    """Delete a plugin."""
    try:
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
