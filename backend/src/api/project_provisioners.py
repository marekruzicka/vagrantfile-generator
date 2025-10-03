"""
Project Provisioner API endpoints for Vagrantfile Generator.

This module contains API endpoints for managing provisioners within projects.
"""

from uuid import UUID
from typing import List

from fastapi import APIRouter, HTTPException, Depends, status

from ..services import ProjectService, ProjectNotFoundError
from ..services.global_provisioner_service import GlobalProvisionerService, GlobalProvisionerServiceError
from ..models.global_provisioner import GlobalProvisionerSummary

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

# Dependency to get GlobalProvisionerService instance
def get_provisioner_service() -> GlobalProvisionerService:
    """Get GlobalProvisionerService instance."""
    return GlobalProvisionerService()


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
