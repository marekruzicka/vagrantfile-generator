"""
VM API endpoints for Vagrantfile GUI Generator.

This module contains API endpoints for managing virtual machines within projects.
"""

from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, Depends, Request

from ..models import VirtualMachine, VirtualMachineCreate, DeploymentStatus
from ..services import ProjectService, ProjectNotFoundError

router = APIRouter()

# Dependency to get ProjectService instance
def get_project_service() -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService()

@router.post("/projects/{project_id}/vms", response_model=VirtualMachine, status_code=201)
async def create_vm(
    project_id: UUID,
    vm_data: dict,  # Accept raw dict instead of VirtualMachineCreate to bypass validation
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    """Add a new VM to a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot add VM - project is locked in ready status")
        
        # Set validation configuration based on request headers BEFORE validation
        from ..models.network_interface import set_validation_config, get_validation_config
        validation_config = {
            "allow_public_ips_in_private_networks": request.headers.get("X-Allow-Public-IPs") == "true"
        }
        set_validation_config(validation_config)
        
        # Now create VirtualMachineCreate from the dict (validation happens here)
        vm_create = VirtualMachineCreate(**vm_data)
        
        # Create VirtualMachine instance from the validated data
        vm = VirtualMachine(**vm_create.dict())
        
        # Add to project
        project = project_service.add_vm_to_project(project_id, vm)
        
        # Return the created VM
        added_vm = project.get_vm(vm.name)
        if not added_vm:
            raise HTTPException(status_code=500, detail="Failed to add VM to project")
        
        return added_vm
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

@router.put("/projects/{project_id}/vms/{vm_name}", response_model=VirtualMachine)
async def update_vm(
    project_id: UUID,
    vm_name: str,
    vm_data: dict,  # Accept raw dict instead of VirtualMachineCreate to bypass validation
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update a VM in a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot modify VM - project is locked in ready status")
        
        # Set validation configuration based on request headers BEFORE validation
        from ..models.network_interface import set_validation_config
        validation_config = {
            "allow_public_ips_in_private_networks": request.headers.get("X-Allow-Public-IPs") == "true"
        }
        set_validation_config(validation_config)
        
        # Now create VirtualMachineCreate from the dict (validation happens here)
        vm_create = VirtualMachineCreate(**vm_data)
        
        # Update VM in project (validation happens during model creation)
        project = project_service.update_vm_in_project(
            project_id, 
            vm_name, 
            vm_create.dict()
        )
        
        # Return the updated VM
        updated_vm = project.get_vm(vm_name)
        if not updated_vm:
            raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found in project")
        
        return updated_vm
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/projects/{project_id}/vms/{vm_name}", status_code=204)
async def delete_vm(
    project_id: UUID,
    vm_name: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Remove a VM from a project."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot delete VM - project is locked in ready status")
        
        project_service.remove_vm_from_project(project_id, vm_name)
        return None  # 204 No Content
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/projects/{project_id}/vms/{vm_name}/network-interfaces", response_model=dict, status_code=201)
async def add_network_interface(
    project_id: UUID,
    vm_name: str,
    interface_data: Dict[str, Any],
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    """Add a network interface to a VM."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot add network interface - project is locked in ready status")
        
        # Set validation configuration based on request headers BEFORE creating interface
        from ..models.network_interface import set_validation_config
        validation_config = {
            "allow_public_ips_in_private_networks": request.headers.get("X-Allow-Public-IPs") == "true"
        }
        set_validation_config(validation_config)
        
        # This is a simplified implementation
        # In a full implementation, you would create a NetworkInterface model
        # and add it to the VM
        
        from ..models import NetworkInterface
        interface = NetworkInterface(**interface_data)
        
        project = project_service.get_project(project_id)
        vm = project.get_vm(vm_name)
        
        if not vm:
            raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found in project")
        
        vm.add_network_interface(interface)
        
        # Save the updated project
        project_service._save_project_to_file(project)
        
        return interface.dict()
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/projects/{project_id}/vms/{vm_name}/network-interfaces/{interface_id}", response_model=dict)
async def update_network_interface(
    project_id: UUID,
    vm_name: str,
    interface_id: str,
    interface_data: Dict[str, Any],
    request: Request,
    project_service: ProjectService = Depends(get_project_service)
):
    """Update a network interface on a VM."""
    try:
        # Check if project is locked
        existing_project = project_service.get_project(project_id)
        if existing_project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot modify network interface - project is locked in ready status")
        
        # Set validation configuration based on request headers BEFORE validation
        from ..models.network_interface import set_validation_config
        validation_config = {
            "allow_public_ips_in_private_networks": request.headers.get("X-Allow-Public-IPs") == "true"
        }
        set_validation_config(validation_config)
        
        project = project_service.get_project(project_id)
        vm = project.get_vm(vm_name)
        
        if not vm:
            raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found in project")
        
        # Find and update the interface
        for interface in vm.network_interfaces:
            if getattr(interface, 'id', None) == interface_id:
                # Update interface fields
                for field, value in interface_data.items():
                    if hasattr(interface, field):
                        setattr(interface, field, value)
                
                # Save the updated project
                project_service._save_project_to_file(project)
                
                return interface.dict()
        
        raise HTTPException(status_code=404, detail=f"Network interface '{interface_id}' not found")
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/projects/{project_id}/vms/{vm_name}/network-interfaces/{interface_id}", status_code=204)
async def delete_network_interface(
    project_id: UUID,
    vm_name: str,
    interface_id: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """Remove a network interface from a VM."""
    try:
        project = project_service.get_project(project_id)
        
        # Check if project is locked
        if project.deployment_status == DeploymentStatus.READY:
            raise HTTPException(status_code=400, detail="Cannot delete network interface - project is locked in ready status")
        
        vm = project.get_vm(vm_name)
        
        if not vm:
            raise HTTPException(status_code=404, detail=f"VM '{vm_name}' not found in project")
        
        success = vm.remove_network_interface(interface_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Network interface '{interface_id}' not found")
        
        # Save the updated project
        project_service._save_project_to_file(project)
        
        return None  # 204 No Content
        
    except ProjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))