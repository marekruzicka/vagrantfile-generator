"""
Box management API endpoints for Vagrantfile Generator.
"""

from typing import List
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from ..models.box import Box, BoxCreate, BoxUpdate, BoxSummary
from ..services.box_service import BoxService, BoxServiceError

router = APIRouter()
box_service = BoxService()


@router.get("/boxes", response_model=List[BoxSummary])
async def list_boxes():
    """Get list of all boxes."""
    try:
        boxes = box_service.list_boxes()
        return boxes
    except BoxServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/boxes/{box_id}", response_model=Box)
async def get_box(box_id: str):
    """Get a specific box by ID."""
    try:
        box = box_service.get_box(box_id)
        if not box:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Box with ID {box_id} not found"
            )
        return box
    except BoxServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/boxes", response_model=Box, status_code=status.HTTP_201_CREATED)
async def create_box(box_data: BoxCreate):
    """Create a new box."""
    try:
        box = box_service.create_box(box_data)
        return box
    except BoxServiceError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/boxes/{box_id}", response_model=Box)
async def update_box(box_id: str, box_data: BoxUpdate):
    """Update an existing box."""
    try:
        box = box_service.update_box(box_id, box_data)
        if not box:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Box with ID {box_id} not found"
            )
        return box
    except BoxServiceError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/boxes/{box_id}")
async def delete_box(box_id: str):
    """Delete a box."""
    try:
        deleted = box_service.delete_box(box_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Box with ID {box_id} not found"
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": f"Box {box_id} deleted successfully"}
        )
    except BoxServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )