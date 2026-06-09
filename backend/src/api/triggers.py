"""
Global Trigger API endpoints for Vagrantfile Generator.

This module provides REST API endpoints for managing global triggers.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends

from ..models.user_profile import UserProfile
from ..middleware.auth_middleware import get_optional_user

from ..models.global_trigger import (
    GlobalTrigger,
    GlobalTriggerCreate,
    GlobalTriggerUpdate,
    GlobalTriggerSummary
)
from ..services.global_trigger_service import GlobalTriggerService, GlobalTriggerServiceError


router = APIRouter()

# Dependency to get GlobalTriggerService instance
def get_trigger_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> GlobalTriggerService:
    """Get GlobalTriggerService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return GlobalTriggerService(user_id=user_id)


@router.post("/triggers", response_model=GlobalTrigger, status_code=status.HTTP_201_CREATED)
async def create_trigger(
    trigger_data: GlobalTriggerCreate,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Create a new global trigger.
    
    Args:
        trigger_data: Trigger creation data
        
    Returns:
        Created trigger
        
    Raises:
        HTTPException: If trigger with same name already exists
    """
    try:
        trigger = trigger_service.create_trigger(trigger_data)
        return trigger
    except GlobalTriggerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create trigger: {str(e)}"
        )


@router.get("/triggers", response_model=List[GlobalTriggerSummary])
async def list_triggers(
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    List all global triggers.
    
    Returns:
        List of trigger summaries
    """
    try:
        triggers = trigger_service.list_triggers_summary()
        return triggers
    except GlobalTriggerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/triggers/{trigger_id}", response_model=GlobalTrigger)
async def get_trigger(
    trigger_id: str,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Get a specific trigger by ID.
    
    Args:
        trigger_id: Trigger ID
        
    Returns:
        Trigger details
        
    Raises:
        HTTPException: If trigger not found
    """
    try:
        trigger = trigger_service.get_trigger(trigger_id)
        
        if not trigger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger with ID {trigger_id} not found"
            )
        
        return trigger
    except HTTPException:
        raise
    except GlobalTriggerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/triggers/{trigger_id}", response_model=GlobalTrigger)
async def update_trigger(
    trigger_id: str,
    trigger_data: GlobalTriggerUpdate,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Update an existing trigger.
    
    Args:
        trigger_id: Trigger ID to update
        trigger_data: Updated trigger data
        
    Returns:
        Updated trigger
        
    Raises:
        HTTPException: If trigger not found or name conflict
    """
    try:
        # Check if trigger is shared (read-only)
        if trigger_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_path = file_service.get_shared_data_path("triggers") / f"{trigger_id}.json"
            if shared_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot modify shared resource - shared resources are read-only"
                )
        
        trigger = trigger_service.update_trigger(trigger_id, trigger_data)
        return trigger
    except GlobalTriggerServiceError as e:
        # Check if it's a not found error
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update trigger: {str(e)}"
        )


@router.delete("/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_trigger(
    trigger_id: str,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    # Delete a trigger.
    try:
        # Check if trigger is shared (read-only)
        if trigger_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_path = file_service.get_shared_data_path("triggers") / f"{trigger_id}.json"
            if shared_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete shared resource - shared resources are read-only"
                )
        
        success = trigger_service.delete_trigger(trigger_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger with ID {trigger_id} not found"
            )
        return None
    except HTTPException:
        raise
    except GlobalTriggerServiceError as e:
        # Provide user-friendly response if trigger missing
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete trigger: {str(e)}"
        )


@router.post("/triggers/{trigger_id}/copy", response_model=GlobalTrigger)
async def copy_shared_trigger(
    trigger_id: str,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Copy a shared trigger to user's directory.
    User can then edit/customize their copy.
    """
    try:
        copied_trigger = trigger_service.copy_shared_trigger(trigger_id)
        return copied_trigger
    except GlobalTriggerServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/triggers/copies-of/{source_id}", response_model=List[GlobalTrigger])
async def get_copies_of_shared_trigger(
    source_id: str,
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Get all user's copies of a specific shared trigger.
    Useful for showing existing copies before creating a new one.
    """
    try:
        copies = trigger_service.get_copies_of_shared_resource(source_id)
        return copies
    except GlobalTriggerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
