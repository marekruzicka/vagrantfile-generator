"""
Configuration API endpoints.

Provides public endpoints for retrieving application configuration.
Also handles user preferences.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..utils.deployment import get_deployment_mode, DeploymentMode
from ..models.user_profile import UserProfile
from ..middleware.auth_middleware import get_current_user, get_optional_user
from ..services.preference_service import PreferenceService, UserPreferences
from ..utils.deployment import is_self_hosted_mode


router = APIRouter(prefix="/api/config", tags=["config"])


class DeploymentModeResponse(BaseModel):
    """Deployment mode response model."""
    mode: str


@router.get("/deployment-mode", response_model=DeploymentModeResponse)
async def get_deployment_mode_endpoint():
    """
    Get the current deployment mode.
    
    Returns:
        DeploymentModeResponse: The deployment mode (self-hosted or public)
    """
    mode = get_deployment_mode()
    return DeploymentModeResponse(mode=mode.value)


# Preference endpoints

@router.get("/preferences", response_model=UserPreferences)
async def get_preferences(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Get user preferences.
    
    In self-hosted mode, returns default preferences.
    In public mode, returns user's personalized preferences.
    
    Returns:
        UserPreferences: User's preferences or defaults
    """
    try:
        # In self-hosted mode, return default preferences
        if is_self_hosted_mode() or current_user is None:
            return UserPreferences(
                show_shared_resources=True,
                favorite_plugins=[],
                favorite_provisioners=[],
                favorite_triggers=[],
                favorite_boxes=[]
            )
        
        # In public mode, return user's preferences
        pref_service = PreferenceService(current_user.user_id)
        return pref_service.get_preferences()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.put("/preferences", response_model=UserPreferences)
async def update_preferences(
    preferences: UserPreferences,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Update user preferences.
    
    In self-hosted mode, returns the provided preferences (no storage).
    In public mode, saves and returns user's preferences.
    
    Args:
        preferences: New preferences
        
    Returns:
        UserPreferences: Updated preferences
    """
    try:
        # In self-hosted mode, just return the preferences (don't save)
        if is_self_hosted_mode() or current_user is None:
            return preferences
        
        # In public mode, save user's preferences
        pref_service = PreferenceService(current_user.user_id)
        return pref_service.update_preferences(preferences)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preferences: {str(e)}"
        )


class ShowSharedResponse(BaseModel):
    """Response for show_shared_resources preference."""
    show_shared_resources: bool


@router.get("/preferences/show-shared", response_model=ShowSharedResponse)
async def get_show_shared_preference(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Get the show_shared_resources preference.
    
    In self-hosted mode, always returns true.
    In public mode, returns user's preference.
    
    Returns:
        ShowSharedResponse: The preference value
    """
    try:
        # In self-hosted mode, always show shared resources
        if is_self_hosted_mode() or current_user is None:
            return ShowSharedResponse(show_shared_resources=True)
        
        # In public mode, return user's preference
        pref_service = PreferenceService(current_user.user_id)
        show_shared = pref_service.get_show_shared_resources()
        return ShowSharedResponse(show_shared_resources=show_shared)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preference: {str(e)}"
        )


@router.put("/preferences/show-shared", response_model=ShowSharedResponse)
async def set_show_shared_preference(
    request: ShowSharedResponse,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Set the show_shared_resources preference.
    
    In self-hosted mode, returns the requested value (no storage).
    In public mode, saves and returns user's preference.
    
    Args:
        request: The new preference value
        
    Returns:
        ShowSharedResponse: The updated preference value
    """
    try:
        # In self-hosted mode, just return the value (don't save)
        if is_self_hosted_mode() or current_user is None:
            return request
        
        # In public mode, save user's preference
        pref_service = PreferenceService(current_user.user_id)
        show_shared = pref_service.set_show_shared_resources(request.show_shared_resources)
        return ShowSharedResponse(show_shared_resources=show_shared)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update preference: {str(e)}"
        )


# Favorites endpoints

class FavoritesRequest(BaseModel):
    """Request to add/remove a favorite."""
    resource_id: str


class FavoritesResponse(BaseModel):
    """Response for favorites operations."""
    resource_type: str
    resource_id: str
    is_favorite: bool


@router.get("/preferences/favorites/{resource_type}")
async def get_favorites(
    resource_type: str,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Get list of favorite resource IDs for a resource type.
    
    In self-hosted mode, returns empty list.
    In public mode, returns user's favorites.
    
    Args:
        resource_type: Type of resource (plugins, provisioners, triggers, boxes)
        
    Returns:
        List of favorite resource IDs
    """
    if resource_type not in ['plugins', 'provisioners', 'triggers', 'boxes']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}"
        )
    
    try:
        # In self-hosted mode, return empty favorites list
        if is_self_hosted_mode() or current_user is None:
            return {"resource_type": resource_type, "favorites": []}
        
        # In public mode, return user's favorites
        pref_service = PreferenceService(current_user.user_id)
        favorites = pref_service.get_favorites(resource_type)
        return {"resource_type": resource_type, "favorites": favorites}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get favorites: {str(e)}"
        )


@router.post("/preferences/favorites/{resource_type}/add", response_model=FavoritesResponse)
async def add_favorite(
    resource_type: str,
    request: FavoritesRequest,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Add a resource to favorites.
    
    In self-hosted mode, returns success without storing.
    In public mode, saves the favorite.
    
    Args:
        resource_type: Type of resource (plugins, provisioners, triggers, boxes)
        request: Resource ID to add
        
    Returns:
        FavoritesResponse: Updated favorite status
    """
    if resource_type not in ['plugins', 'provisioners', 'triggers', 'boxes']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}"
        )
    
    try:
        # In self-hosted mode, just return success (don't save)
        if is_self_hosted_mode() or current_user is None:
            return FavoritesResponse(
                resource_type=resource_type,
                resource_id=request.resource_id,
                is_favorite=True
            )
        
        # In public mode, save the favorite
        pref_service = PreferenceService(current_user.user_id)
        pref_service.add_favorite(resource_type, request.resource_id)
        return FavoritesResponse(
            resource_type=resource_type,
            resource_id=request.resource_id,
            is_favorite=True
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add favorite: {str(e)}"
        )


@router.post("/preferences/favorites/{resource_type}/remove", response_model=FavoritesResponse)
async def remove_favorite(
    resource_type: str,
    request: FavoritesRequest,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Remove a resource from favorites.
    
    In self-hosted mode, returns success without storing.
    In public mode, removes the favorite.
    
    Args:
        resource_type: Type of resource (plugins, provisioners, triggers, boxes)
        request: Resource ID to remove
        
    Returns:
        FavoritesResponse: Updated favorite status
    """
    if resource_type not in ['plugins', 'provisioners', 'triggers', 'boxes']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}"
        )
    
    try:
        # In self-hosted mode, just return success (don't save)
        if is_self_hosted_mode() or current_user is None:
            return FavoritesResponse(
                resource_type=resource_type,
                resource_id=request.resource_id,
                is_favorite=False
            )
        
        # In public mode, remove the favorite
        pref_service = PreferenceService(current_user.user_id)
        pref_service.remove_favorite(resource_type, request.resource_id)
        return FavoritesResponse(
            resource_type=resource_type,
            resource_id=request.resource_id,
            is_favorite=False
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove favorite: {str(e)}"
        )


@router.get("/preferences/favorites/{resource_type}/check/{resource_id}")
async def check_favorite(
    resource_type: str,
    resource_id: str,
    current_user: Optional[UserProfile] = Depends(get_optional_user)
):
    """
    Check if a resource is favorited.
    
    In self-hosted mode, always returns false.
    In public mode, checks user's favorites.
    
    Args:
        resource_type: Type of resource (plugins, provisioners, triggers, boxes)
        resource_id: Resource ID to check
        
    Returns:
        FavoritesResponse: Favorite status
    """
    if resource_type not in ['plugins', 'provisioners', 'triggers', 'boxes']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid resource type: {resource_type}"
        )
    
    try:
        # In self-hosted mode, no favorites
        if is_self_hosted_mode() or current_user is None:
            return FavoritesResponse(
                resource_type=resource_type,
                resource_id=resource_id,
                is_favorite=False
            )
        
        # In public mode, check user's favorites
        pref_service = PreferenceService(current_user.user_id)
        is_fav = pref_service.is_favorite(resource_type, resource_id)
        return FavoritesResponse(
            resource_type=resource_type,
            resource_id=resource_id,
            is_favorite=is_fav
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check favorite: {str(e)}"
        )
