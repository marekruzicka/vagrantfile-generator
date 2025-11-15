"""Box management API endpoints for Vagrantfile Generator."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse

from ..models.user_profile import UserProfile
from ..models.box import Box, BoxCreate, BoxUpdate, BoxSummary
from ..services.box_service import BoxService, BoxServiceError
from ..middleware.auth_middleware import get_optional_user

router = APIRouter()

# Dependency to get BoxService instance
def get_box_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> BoxService:
    """Get BoxService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return BoxService(user_id=user_id)


@router.get("/boxes", response_model=List[BoxSummary])
async def list_boxes(box_service: BoxService = Depends(get_box_service)):
    # Get list of all boxes.
    try:
        boxes = box_service.list_boxes()
        return boxes
    except BoxServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/boxes/{box_id}", response_model=Box)
async def get_box(
    box_id: str,
    box_service: BoxService = Depends(get_box_service)
):
    # Get a specific box by ID.
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
async def create_box(
    box_data: BoxCreate,
    box_service: BoxService = Depends(get_box_service)
):
    # Create a new box.
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
async def update_box(
    box_id: str,
    box_data: BoxUpdate,
    box_service: BoxService = Depends(get_box_service)
):
    # Update an existing box.
    try:
        # Check if box is shared (read-only)
        # Boxes use a single JSON file, so we check if service is using shared directory
        if box_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_boxes_file = file_service.get_shared_data_path("boxes") / "boxes.json"
            if shared_boxes_file.exists():
                # Check if this box_id exists in shared boxes
                import json
                with open(shared_boxes_file, 'r') as f:
                    shared_boxes = json.load(f)
                if any(box.get('id') == box_id for box in shared_boxes):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Cannot modify shared resource - shared resources are read-only"
                    )
        
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
async def delete_box(
    box_id: str,
    box_service: BoxService = Depends(get_box_service)
):
    # Delete a box.
    try:
        # Check if box is shared (read-only)
        if box_service.user_id is not None:
            from ..services.file_service import FileService
            file_service = FileService()
            shared_path = file_service.get_shared_data_path("boxes") / f"{box_id}.json"
            if shared_path.exists():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete shared resource - shared resources are read-only"
                )
        
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


@router.post("/boxes/{box_id}/copy", response_model=Box)
async def copy_shared_box(
    box_id: str,
    box_service: BoxService = Depends(get_box_service)
):
    """
    Copy a shared box to user's directory.
    User can then edit/customize their copy.
    """
    try:
        copied_box = box_service.copy_shared_box(box_id)
        return copied_box
    except BoxServiceError as e:
        if "not found" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/boxes/copies-of/{source_id}", response_model=List[Box])
async def get_copies_of_shared_box(
    source_id: str,
    box_service: BoxService = Depends(get_box_service)
):
    """
    Get all user's copies of a specific shared box.
    Useful for showing existing copies before creating a new one.
    """
    try:
        copies = box_service.get_copies_of_shared_resource(source_id)
        return copies
    except BoxServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
