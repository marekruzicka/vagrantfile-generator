"""
Global Provisioner API endpoints for Vagrantfile GUI Generator.

This module provides REST API endpoints for managing global provisioners.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status

from ..models.global_provisioner import (
    GlobalProvisioner,
    GlobalProvisionerCreate,
    GlobalProvisionerUpdate,
    GlobalProvisionerSummary
)
from ..services.global_provisioner_service import GlobalProvisionerService, GlobalProvisionerServiceError


router = APIRouter()
provisioner_service = GlobalProvisionerService()


@router.post("/provisioners", response_model=GlobalProvisioner, status_code=status.HTTP_201_CREATED)
async def create_provisioner(provisioner_data: GlobalProvisionerCreate):
    """
    Create a new global provisioner.
    
    Args:
        provisioner_data: Provisioner creation data
        
    Returns:
        Created provisioner
        
    Raises:
        HTTPException: If provisioner with same name already exists
    """
    try:
        provisioner = provisioner_service.create_provisioner(provisioner_data)
        return provisioner
    except GlobalProvisionerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create provisioner: {str(e)}"
        )


@router.get("/provisioners", response_model=List[GlobalProvisionerSummary])
async def list_provisioners():
    """
    List all global provisioners.
    
    Returns:
        List of provisioner summaries
    """
    try:
        provisioners = provisioner_service.list_provisioners_summary()
        return provisioners
    except GlobalProvisionerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/provisioners/{provisioner_id}", response_model=GlobalProvisioner)
async def get_provisioner(provisioner_id: str):
    """
    Get a specific provisioner by ID.
    
    Args:
        provisioner_id: Provisioner ID
        
    Returns:
        Provisioner details
        
    Raises:
        HTTPException: If provisioner not found
    """
    try:
        provisioner = provisioner_service.get_provisioner(provisioner_id)
        
        if not provisioner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provisioner with ID {provisioner_id} not found"
            )
        
        return provisioner
    except HTTPException:
        raise
    except GlobalProvisionerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/provisioners/{provisioner_id}", response_model=GlobalProvisioner)
async def update_provisioner(provisioner_id: str, provisioner_data: GlobalProvisionerUpdate):
    """
    Update an existing provisioner.
    
    Args:
        provisioner_id: Provisioner ID
        provisioner_data: Provisioner update data
        
    Returns:
        Updated provisioner
        
    Raises:
        HTTPException: If provisioner not found or update fails
    """
    try:
        provisioner = provisioner_service.update_provisioner(provisioner_id, provisioner_data)
        
        if not provisioner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provisioner with ID {provisioner_id} not found"
            )
        
        return provisioner
    except HTTPException:
        raise
    except GlobalProvisionerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update provisioner: {str(e)}"
        )


@router.delete("/provisioners/{provisioner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_provisioner(provisioner_id: str):
    """
    Delete a provisioner.
    
    Args:
        provisioner_id: Provisioner ID
        
    Raises:
        HTTPException: If provisioner not found
    """
    try:
        deleted = provisioner_service.delete_provisioner(provisioner_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Provisioner with ID {provisioner_id} not found"
            )
        
        return None
    except HTTPException:
        raise
    except GlobalProvisionerServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
