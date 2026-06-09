"""
Project Trigger API endpoints for Vagrantfile Generator.

This module provides REST API endpoints for managing triggers on projects.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status

from ..models.global_trigger import GlobalTriggerSummary
from ..models.user_profile import UserProfile
from ..services.project_service import ProjectService, ProjectNotFoundError
from ..services.global_trigger_service import GlobalTriggerService, GlobalTriggerServiceError
from ..middleware.auth_middleware import get_optional_user


router = APIRouter()


def get_project_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> ProjectService:
    """Dependency to get project service instance with user context."""
    user_id = current_user.user_id if current_user else None
    return ProjectService(user_id=user_id)


def get_trigger_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> GlobalTriggerService:
    """Dependency to get trigger service instance with user context."""
    user_id = current_user.user_id if current_user else None
    return GlobalTriggerService(user_id=user_id)


@router.get("/projects/{project_id}/triggers", response_model=List[GlobalTriggerSummary])
async def get_project_triggers(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Get all triggers assigned to a project.
    
    Args:
        project_id: Project ID
        project_service: Project service instance
        trigger_service: Trigger service instance
        
    Returns:
        List of trigger summaries for this project
    """
    try:
        project = project_service.get_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with ID {project_id} not found"
            )
        
        # Get full trigger details
        triggers = []
        for trigger_id in project.global_triggers:
            trigger = trigger_service.get_trigger(trigger_id)
            if trigger:
                triggers.append(GlobalTriggerSummary(
                    id=trigger.id,
                    name=trigger.name,
                    description=trigger.description,
                    timing=trigger.trigger_config.timing,
                    stage=trigger.trigger_config.stage,
                    created_at=trigger.created_at,
                    updated_at=trigger.updated_at
                ))
        
        return triggers
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get project triggers: {str(e)}"
        )


@router.post("/projects/{project_id}/triggers/{trigger_id}", status_code=status.HTTP_201_CREATED)
async def add_trigger_to_project(
    project_id: UUID,
    trigger_id: str,
    project_service: ProjectService = Depends(get_project_service),
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Add a trigger to a project.
    
    Args:
        project_id: Project ID
        trigger_id: Trigger ID to add (from URL path)
        project_service: Project service instance
        trigger_service: Trigger service instance
        
    Returns:
        Updated project
    """
    try:
        # Verify trigger exists
        trigger = trigger_service.get_trigger(trigger_id)
        if not trigger:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger with ID {trigger_id} not found"
            )
        
        # Add trigger to project
        project = project_service.add_trigger_to_project(project_id, trigger_id)
        return {"message": "Trigger added successfully", "project": project}
        
    except HTTPException:
        raise
    except ValueError as e:
        if "already" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e)
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add trigger to project: {str(e)}"
        )


@router.delete("/projects/{project_id}/triggers/{trigger_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_trigger_from_project(
    project_id: UUID,
    trigger_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Remove a trigger from a project.
    
    Args:
        project_id: Project ID
        trigger_id: Trigger ID to remove
        project_service: Project service instance
    """
    try:
        project_service.remove_trigger_from_project(project_id, trigger_id)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove trigger from project: {str(e)}"
        )


@router.post("/projects/{project_id}/triggers/{trigger_id}/copy", response_model=dict)
async def copy_and_replace_trigger_in_project(
    project_id: UUID,
    trigger_id: str,
    project_service: ProjectService = Depends(get_project_service),
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Copy a shared trigger to user's library and update project to reference the copy.
    This enables seamless editing of shared triggers within a project context.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Get the shared trigger
        shared_trigger = trigger_service.get_trigger(trigger_id)
        if not shared_trigger:
            raise HTTPException(status_code=404, detail=f"Trigger {trigger_id} not found")
        
        if not shared_trigger.is_shared:
            raise HTTPException(status_code=400, detail="Trigger is already user-owned, no need to copy")
        
        # Copy the trigger to user's library
        copied_trigger = trigger_service.copy_shared_trigger(trigger_id)
        
        # Update project to reference the new copy
        project_service.update_trigger_in_project(project_id, trigger_id, copied_trigger.id)
        
        return {
            "old_id": trigger_id,
            "new_id": copied_trigger.id,
            "project_updated": True
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except GlobalTriggerServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/triggers/{old_id}/replace/{new_id}", response_model=dict)
async def replace_trigger_in_project(
    project_id: UUID,
    old_id: str,
    new_id: str,
    project_service: ProjectService = Depends(get_project_service),
    trigger_service: GlobalTriggerService = Depends(get_trigger_service)
):
    """
    Replace a trigger reference in a project with a different trigger.
    Useful for reusing an existing user copy instead of creating a new one.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Verify the new trigger exists
        new_trigger = trigger_service.get_trigger(new_id)
        if not new_trigger:
            raise HTTPException(status_code=404, detail=f"Trigger '{new_id}' not found")
        
        # Update the project
        project_service.update_trigger_in_project(project_id, old_id, new_id)
        
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
