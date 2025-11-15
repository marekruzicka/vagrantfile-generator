"""
Project Provisioner API endpoints for Vagrantfile Generator.

This module contains API endpoints for managing provisioners within projects.
"""

from uuid import UUID
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, status

from ..services import ProjectService, ProjectNotFoundError
from ..services.global_provisioner_service import GlobalProvisionerService, GlobalProvisionerServiceError
from ..models.global_provisioner import GlobalProvisionerSummary
from ..models.user_profile import UserProfile
from ..middleware.auth_middleware import get_optional_user

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> ProjectService:
    """Get ProjectService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return ProjectService(user_id=user_id)

# Dependency to get GlobalProvisionerService instance
def get_provisioner_service(
    current_user: Optional[UserProfile] = Depends(get_optional_user)
) -> GlobalProvisionerService:
    """Get GlobalProvisionerService instance with user context."""
    user_id = current_user.user_id if current_user else None
    return GlobalProvisionerService(user_id=user_id)


@router.get("/projects/{project_id}/provisioners", response_model=List[GlobalProvisionerSummary])
async def get_project_provisioners(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    provisioner_service: GlobalProvisionerService = Depends(get_provisioner_service)
):
    """Get all provisioners for a project."""
    try:
        project = project_service.get_project(project_id)
        provisioners = []
        
        for provisioner_id in project.global_provisioners:
            try:
                provisioner = provisioner_service.get_provisioner(provisioner_id)
                provisioners.append(GlobalProvisionerSummary(
                    id=provisioner.id,
                    name=provisioner.name,
                    description=provisioner.description,
                    type=provisioner.type,
                    scope=provisioner.scope
                ))
            except GlobalProvisionerServiceError:
                # Skip provisioners that no longer exist
                continue
        
        return provisioners
        
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/provisioners/{provisioner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def add_provisioner_to_project(
    project_id: UUID,
    provisioner_id: str,
    project_service: ProjectService = Depends(get_project_service),
    provisioner_service: GlobalProvisionerService = Depends(get_provisioner_service)
):
    """Add a provisioner to a project."""
    try:
        # Verify provisioner exists
        try:
            provisioner_service.get_provisioner(provisioner_id)
        except GlobalProvisionerServiceError:
            raise HTTPException(status_code=404, detail=f"Provisioner with ID {provisioner_id} not found")
        
        # Add provisioner to project
        project_service.add_provisioner_to_project(project_id, provisioner_id)
        return None
        
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_id}/provisioners/{provisioner_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_provisioner_from_project(
    project_id: UUID,
    provisioner_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Remove a provisioner from a project."""
    try:
        project_service.remove_provisioner_from_project(project_id, provisioner_id)
        return None
        
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/provisioners/{provisioner_id}/copy", response_model=dict)
async def copy_and_replace_provisioner_in_project(
    project_id: UUID,
    provisioner_id: str,
    project_service: ProjectService = Depends(get_project_service),
    provisioner_service: GlobalProvisionerService = Depends(get_provisioner_service)
):
    """
    Copy a shared provisioner to user's library and update project to reference the copy.
    This enables seamless editing of shared provisioners within a project context.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Get the shared provisioner
        shared_provisioner = provisioner_service.get_provisioner(provisioner_id)
        if not shared_provisioner:
            raise HTTPException(status_code=404, detail=f"Provisioner {provisioner_id} not found")
        
        if not shared_provisioner.is_shared:
            raise HTTPException(status_code=400, detail="Provisioner is already user-owned, no need to copy")
        
        # Copy the provisioner to user's library
        copied_provisioner = provisioner_service.copy_shared_provisioner(provisioner_id)
        
        # Update project to reference the new copy
        project_service.update_provisioner_in_project(project_id, provisioner_id, copied_provisioner.id)
        
        return {
            "old_id": provisioner_id,
            "new_id": copied_provisioner.id,
            "project_updated": True
        }
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except GlobalProvisionerServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/provisioners/{old_id}/replace/{new_id}", response_model=dict)
async def replace_provisioner_in_project(
    project_id: UUID,
    old_id: str,
    new_id: str,
    project_service: ProjectService = Depends(get_project_service),
    provisioner_service: GlobalProvisionerService = Depends(get_provisioner_service)
):
    """
    Replace a provisioner reference in a project with a different provisioner.
    Useful for reusing an existing user copy instead of creating a new one.
    
    Returns:
        Dictionary with old_id, new_id, and project_updated flag
    """
    try:
        # Verify the new provisioner exists
        new_provisioner = provisioner_service.get_provisioner(new_id)
        if not new_provisioner:
            raise HTTPException(status_code=404, detail=f"Provisioner '{new_id}' not found")
        
        # Update the project
        project_service.update_provisioner_in_project(project_id, old_id, new_id)
        
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
