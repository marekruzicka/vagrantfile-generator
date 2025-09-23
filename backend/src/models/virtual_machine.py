"""
VirtualMachine model for Vagrantfile GUI Generator.

This module defines the VirtualMachine entity and related models that represent
a single VM configuration within a Vagrant project.
"""

from typing import List, Optional, Tuple
import re

from pydantic import BaseModel, Field, validator


class VirtualMachineBase(BaseModel):
    """Base class for VirtualMachine with shared fields."""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique VM identifier"
    )
    box: str = Field(
        ...,
        min_length=1,
        description="Vagrant box name (e.g., 'ubuntu/jammy64')"
    )
    hostname: Optional[str] = Field(
        default=None,
        max_length=50,
        description="VM hostname (defaults to name if not specified)"
    )
    memory: int = Field(
        default=1024,
        ge=512,
        le=32768,
        description="RAM in MB (minimum 512 MB)"
    )
    cpus: int = Field(
        default=1,
        ge=1,
        le=16,
        description="CPU count (minimum 1)"
    )

    @validator('name')
    def validate_vm_name(cls, v):
        """Ensure VM name is valid for Vagrant."""
        if not v:
            raise ValueError("VM name cannot be empty")
        
        # VM names should be alphanumeric with underscores and hyphens
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("VM name can only contain letters, numbers, underscores, and hyphens")
        
        # Cannot start with number or special character
        if not v[0].isalpha():
            raise ValueError("VM name must start with a letter")
        
        return v

    @validator('box')
    def validate_box_name(cls, v):
        """Ensure box name is valid."""
        if not v or not v.strip():
            raise ValueError("Box name cannot be empty")
        return v.strip()

    @validator('hostname')
    def validate_hostname(cls, v):
        """Validate hostname format if provided."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Basic hostname validation
        if not re.match(r'^[a-zA-Z0-9.-]+$', v):
            raise ValueError("Hostname can only contain letters, numbers, dots, and hyphens")
        
        if len(v) > 253:
            raise ValueError("Hostname too long (max 253 characters)")
        
        return v


class VirtualMachineCreate(VirtualMachineBase):
    """Schema for creating a new VM."""
    network_interfaces: List['NetworkInterface'] = Field(
        default_factory=list,
        description="Network interface configurations"
    )
    synced_folders: List['SyncedFolder'] = Field(
        default_factory=list,
        description="Host/guest folder mappings"
    )
    provisioners: List['Provisioner'] = Field(
        default_factory=list,
        description="Setup scripts and configurations"
    )
    plugins: List['PluginConfiguration'] = Field(
        default_factory=list,
        description="VM-specific plugin configurations"
    )


class VirtualMachine(VirtualMachineBase):
    """Complete VirtualMachine model with all relationships."""
    
    network_interfaces: List['NetworkInterface'] = Field(
        default_factory=list,
        description="Network interface configurations"
    )
    synced_folders: List['SyncedFolder'] = Field(
        default_factory=list,
        description="Host/guest folder mappings"
    )
    provisioners: List['Provisioner'] = Field(
        default_factory=list,
        description="Setup scripts and configurations"
    )
    plugins: List['PluginConfiguration'] = Field(
        default_factory=list,
        description="VM-specific plugin configurations"
    )

    class Config:
        """Pydantic configuration."""
        schema_extra = {
            "example": {
                "name": "web-server",
                "box": "ubuntu/jammy64",
                "hostname": "web",
                "memory": 2048,
                "cpus": 2,
                "network_interfaces": [],
                "synced_folders": [],
                "provisioners": [],
                "plugins": []
            }
        }

    def get_effective_hostname(self) -> str:
        """Get the hostname, defaulting to VM name if not set."""
        return self.hostname if self.hostname else self.name

    def add_network_interface(self, interface: 'NetworkInterface'):
        """Add a network interface with validation."""
        # Check for conflicts in static IP assignments
        if interface.ip_assignment == "static" and interface.ip_address:
            for existing in self.network_interfaces:
                if (existing.ip_assignment == "static" and 
                    existing.ip_address == interface.ip_address):
                    raise ValueError(f"IP address {interface.ip_address} already assigned to this VM")
        
        self.network_interfaces.append(interface)

    def remove_network_interface(self, interface_id: str) -> bool:
        """Remove a network interface by ID. Returns True if found and removed."""
        for i, interface in enumerate(self.network_interfaces):
            if getattr(interface, 'id', None) == interface_id:
                del self.network_interfaces[i]
                return True
        return False

    def add_synced_folder(self, folder: 'SyncedFolder'):
        """Add a synced folder with validation."""
        # Check for duplicate guest paths
        for existing in self.synced_folders:
            if existing.guest_path == folder.guest_path:
                raise ValueError(f"Guest path '{folder.guest_path}' already mapped in this VM")
        
        self.synced_folders.append(folder)

    def add_provisioner(self, provisioner: 'Provisioner'):
        """Add a provisioner to the VM."""
        self.provisioners.append(provisioner)

    def validate_vm(self) -> Tuple[List[str], List[str]]:
        """
        Validate the VM configuration.
        
        Returns:
            tuple: (errors, warnings)
        """
        errors = []
        warnings = []

        # Validate network interfaces
        static_ips = []
        for interface in self.network_interfaces:
            if interface.ip_assignment == "static":
                if not interface.ip_address:
                    errors.append(f"Static network interface missing IP address")
                else:
                    if interface.ip_address in static_ips:
                        errors.append(f"Duplicate IP address {interface.ip_address}")
                    static_ips.append(interface.ip_address)

        # Check for synced folder conflicts
        guest_paths = []
        for folder in self.synced_folders:
            if folder.guest_path in guest_paths:
                errors.append(f"Duplicate guest path: {folder.guest_path}")
            guest_paths.append(folder.guest_path)

        # Warnings
        if not self.network_interfaces:
            warnings.append("No network interfaces configured")
        
        if self.memory < 1024:
            warnings.append(f"Low memory allocation: {self.memory}MB")
        
        if not self.provisioners:
            warnings.append("No provisioners configured")

        return errors, warnings

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "box": self.box,
            "hostname": self.get_effective_hostname(),
            "memory": self.memory,
            "cpus": self.cpus,
            "network_interfaces": [ni.dict() for ni in self.network_interfaces],
            "synced_folders": [sf.dict() for sf in self.synced_folders],
            "provisioners": [p.dict() for p in self.provisioners],
            "plugins": [p.dict() for p in self.plugins]
        }


# Will be imported by related models
from .network_interface import NetworkInterface
from .synced_folder import SyncedFolder
from .provisioner import Provisioner
from .plugin_configuration import PluginConfiguration

# Update forward references
VirtualMachine.model_rebuild()