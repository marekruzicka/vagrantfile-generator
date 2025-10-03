"""
Project Trigger API endpoints for Vagrantfile Generator.

This module provides REST API endpoints for managing triggers on projects.
"""

from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status

from ..models.global_trigger import GlobalTriggerSummary
from ..services.project_service import ProjectService, ProjectNotFoundError
from ..services.global_trigger_service import GlobalTriggerService, GlobalTriggerServiceError


router = APIRouter()


def get_project_service() -> ProjectService:
    """Dependency to get project service instance."""
    return ProjectService()


def get_trigger_service() -> GlobalTriggerService:
    """Dependency to get trigger service instance."""
    return GlobalTriggerService()


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
