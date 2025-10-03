"""
Global Trigger API endpoints for Vagrantfile Generator.

This module provides REST API endpoints for managing global triggers.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from ..models.global_trigger import (
    GlobalTrigger,
    GlobalTriggerCreate,
    GlobalTriggerUpdate,
    GlobalTriggerSummary
)
from ..services.global_trigger_service import GlobalTriggerService, GlobalTriggerServiceError


router = APIRouter()
trigger_service = GlobalTriggerService()


@router.post("/triggers", response_model=GlobalTrigger, status_code=status.HTTP_201_CREATED)
async def create_trigger(trigger_data: GlobalTriggerCreate):
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
async def list_triggers():
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
async def get_trigger(trigger_id: str):
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
async def update_trigger(trigger_id: str, trigger_data: GlobalTriggerUpdate):
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
async def delete_trigger(trigger_id: str):
    """
    Delete a trigger.
    
    Args:
        trigger_id: Trigger ID to delete
        
    Raises:
        HTTPException: If trigger not found
    """
    try:
        deleted = trigger_service.delete_trigger(trigger_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger with ID {trigger_id} not found"
            )
            
    except HTTPException:
        raise
    except GlobalTriggerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
