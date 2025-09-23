"""
Generation API endpoints for Vagrantfile GUI Generator.

This module contains API endpoints for generating and validating Vagrantfiles.
"""

from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import PlainTextResponse

from ..services import ProjectService, ProjectNotFoundError, VagrantfileGenerator

router = APIRouter()

# Dependencies
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

def get_vagrantfile_generator() -> VagrantfileGenerator:
    """Get VagrantfileGenerator instance."""
    return VagrantfileGenerator()

@router.post("/projects/{project_id}/generate", response_model=dict)
async def generate_vagrantfile(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    generator: VagrantfileGenerator = Depends(get_vagrantfile_generator)
):
    """Generate a Vagrantfile from project configuration."""
    try:
        project = project_service.get_project(project_id)
        result = generator.generate_with_validation(project)
        return result
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/projects/{project_id}/download", response_class=PlainTextResponse)
async def download_vagrantfile(
    project_id: UUID,
    project_service: ProjectService = Depends(get_project_service),
    generator: VagrantfileGenerator = Depends(get_vagrantfile_generator)
):
    """Download a Vagrantfile for the specified project."""
    try:
        project = project_service.get_project(project_id)
        result = generator.generate_with_validation(project)
        
        # Return the content as plain text with appropriate headers
        return PlainTextResponse(
            content=result["content"],
            headers={
                "Content-Disposition": f"attachment; filename={result['filename']}",
                "Content-Type": "text/plain"
            }
        )
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/vagrant/boxes", response_model=dict)
async def get_vagrant_boxes():
    """Get list of popular Vagrant boxes for autocomplete."""
    # This is a static list for now, in production this could come from
    # Vagrant Cloud API or a configurable list
    boxes = [
        {
            "name": "generic/ubuntu2204",
            "description": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
            "provider": "libvirt"
        },
        {
            "name": "generic/ubuntu2004",
            "description": "Ubuntu 20.04 LTS (Focal Fossa)",
            "provider": "libvirt"
        },
        {
            "name": "generic/centos7",
            "description": "CentOS 7",
            "provider": "libvirt"
        },
        {
            "name": "generic/debian12",
            "description": "Debian 12 (Bookworm)",
            "provider": "libvirt"
        },
        {
            "name": "generic/alpine318",
            "description": "Alpine Linux 3.18",
            "provider": "libvirt"
        },
        {
            "name": "generic/fedora38",
            "description": "Fedora 38",
            "provider": "libvirt"
        }
    ]
    
    return {"boxes": boxes}

@router.get("/vagrant/plugins", response_model=dict)
async def get_vagrant_plugins():
    """Get list of popular Vagrant plugins."""
    # Static list of common Vagrant plugins
    plugins = [
        {
            "name": "vagrant-vbguest",
            "description": "Auto-install VirtualBox Guest Additions",
            "category": "virtualbox"
        },
        {
            "name": "vagrant-hostmanager",
            "description": "Manage hosts file entries for VMs",
            "category": "networking"
        },
        {
            "name": "vagrant-cachier",
            "description": "Cache package downloads to speed up provisioning",
            "category": "provisioning"
        },
        {
            "name": "vagrant-disksize",
            "description": "Resize VM disk size",
            "category": "storage"
        },
        {
            "name": "vagrant-env",
            "description": "Load environment variables from .env files",
            "category": "configuration"
        }
    ]
    
    return {"plugins": plugins}