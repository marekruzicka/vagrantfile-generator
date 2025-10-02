"""
Project model for Vagrantfile GUI Generator.

This module defines the Project entity and related Pydantic models for data validation
and serialization. The Project serves as the root container for a complete Vagrant
environment configuration.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from enum import Enum

from pydantic import BaseModel, Field, validator


class DeploymentStatus(str, Enum):
    """Project deployment status enumeration."""
    DRAFT = "draft"
    READY = "ready"


class ProjectBase(BaseModel):
    """Base class for Project with shared fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Human-readable project name"
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Optional project description"
    )
    deployment_status: DeploymentStatus = Field(
        default=DeploymentStatus.DRAFT,
        description="Current deployment status of the project"
    )

    @validator('name')
    def validate_name(cls, v):
        """Ensure project name is a valid filename."""
        if not v:
            raise ValueError("Project name cannot be empty")
        
        # Check for invalid filename characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Project name contains invalid characters: {invalid_chars}")
        
        # Cannot start or end with space/dot
        if v.startswith(' ') or v.endswith(' ') or v.startswith('.') or v.endswith('.'):
            raise ValueError("Project name cannot start or end with space or dot")
        
        return v.strip()


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(ProjectBase):
    """Schema for updating an existing project."""
    version: str = Field(default="1.0.0", description="Data model version")
    vms: List['VirtualMachine'] = Field(default_factory=list)
    global_plugins: List['PluginConfiguration'] = Field(default_factory=list)
    global_provisioners: List[str] = Field(
        default_factory=list,
        description="List of global provisioner IDs applied to all VMs"
    )

    @validator('vms')
    def validate_vm_names_unique(cls, v):
        """Ensure VM names are unique within the project."""
        if not v:
            return v
        
        vm_names = [vm.name for vm in v]
        if len(vm_names) != len(set(vm_names)):
            raise ValueError("VM names must be unique within the project")
        
        return v


class Project(ProjectBase):
    """Complete Project model with all fields."""
    
    id: UUID = Field(default_factory=uuid4, description="Unique project identifier")
    version: str = Field(default="1.0.0", description="Data model version")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    vms: List['VirtualMachine'] = Field(default_factory=list)
    global_plugins: List['PluginConfiguration'] = Field(default_factory=list)
    global_provisioners: List[str] = Field(
        default_factory=list,
        description="List of global provisioner IDs applied to all VMs"
    )

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "my-vagrant-project",
                "description": "A sample project with web and database VMs",
                "version": "1.0.0",
                "created_at": "2025-09-23T10:30:00",
                "updated_at": "2025-09-23T10:30:00",
                "vms": [],
                "global_plugins": []
            }
        }

    @validator('vms')
    def validate_vm_names_unique(cls, v):
        """Ensure VM names are unique within the project."""
        if not v:
            return v
        
        vm_names = [vm.name for vm in v]
        if len(vm_names) != len(set(vm_names)):
            raise ValueError("VM names must be unique within the project")
        
        return v

    def update_timestamp(self):
        """Update the updated_at timestamp to current time."""
        self.updated_at = datetime.utcnow()

    def add_vm(self, vm: 'VirtualMachine'):
        """Add a VM to the project with validation."""
        # Check for duplicate names
        existing_names = [existing_vm.name for existing_vm in self.vms]
        if vm.name in existing_names:
            raise ValueError(f"VM with name '{vm.name}' already exists in project")
        
        self.vms.append(vm)
        self.update_timestamp()

    def remove_vm(self, vm_name: str) -> bool:
        """Remove a VM by name. Returns True if found and removed."""
        for i, vm in enumerate(self.vms):
            if vm.name == vm_name:
                del self.vms[i]
                self.update_timestamp()
                return True
        return False

    def get_vm(self, vm_name: str) -> Optional['VirtualMachine']:
        """Get a VM by name."""
        for vm in self.vms:
            if vm.name == vm_name:
                return vm
        return None

    def validate_for_generation(self) -> tuple[bool, List[str], List[str]]:
        """
        Validate project for Vagrantfile generation.
        
        Returns:
            tuple: (is_valid, errors, warnings)
        """
        errors = []
        warnings = []

        # Must have at least one VM
        if not self.vms:
            errors.append("Project must have at least one virtual machine")

        # Validate each VM
        for vm in self.vms:
            vm_errors, vm_warnings = vm.validate_vm()
            errors.extend([f"VM '{vm.name}': {error}" for error in vm_errors])
            warnings.extend([f"VM '{vm.name}': {warning}" for warning in vm_warnings])

        # Check for IP conflicts across all VMs
        ip_addresses = []
        for vm in self.vms:
            for interface in vm.network_interfaces:
                if interface.ip_assignment == "static" and interface.ip_address:
                    if interface.ip_address in ip_addresses:
                        errors.append(f"IP address conflict: {interface.ip_address} is used by multiple VMs")
                    else:
                        ip_addresses.append(interface.ip_address)

        is_valid = len(errors) == 0
        return is_valid, errors, warnings


class ProjectSummary(BaseModel):
    """Lightweight project model for list views."""
    
    id: UUID
    name: str
    description: str
    created_at: datetime
    updated_at: datetime
    vm_count: int
    deployment_status: DeploymentStatus

    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: str
        }

    @classmethod
    def from_project(cls, project: Project) -> 'ProjectSummary':
        """Create a summary from a full Project instance."""
        return cls(
            id=project.id,
            name=project.name,
            description=project.description,
            created_at=project.created_at,
            updated_at=project.updated_at,
            vm_count=len(project.vms),
            deployment_status=project.deployment_status
        )


# Forward references for circular imports
from .virtual_machine import VirtualMachine
from .plugin_configuration import PluginConfiguration

# Update forward references
Project.model_rebuild()
ProjectUpdate.model_rebuild()