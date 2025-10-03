"""
SyncedFolder model for Vagrantfile Generator.

This module defines synced folder configurations that map host directories
to guest directories in virtual machines.
"""

from typing import Dict, Any, Optional
import os

from pydantic import BaseModel, Field, field_validator


class SyncedFolder(BaseModel):
    """Synced folder configuration model."""
    
    host_path: str = Field(
        ...,
        description="Path on host machine"
    )
    guest_path: str = Field(
        ...,
        description="Path on guest machine"
    )
    disabled: bool = Field(
        default=False,
        description="Whether folder sync is disabled"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional Vagrant sync options"
    )

    @field_validator('host_path')
    @classmethod
    def validate_host_path(cls, v: str) -> str:
        """Validate and normalize host path."""
        if not v or not v.strip():
            raise ValueError("Host path cannot be empty")
        
        v = v.strip()
        
        # Convert to absolute path if relative
        if not os.path.isabs(v):
            # For validation purposes, we'll accept relative paths
            # but warn that they should be absolute
            pass
        
        return v

    @field_validator('guest_path')
    @classmethod
    def validate_guest_path(cls, v: str) -> str:
        """Validate guest path format."""
        if not v or not v.strip():
            raise ValueError("Guest path cannot be empty")
        
        v = v.strip()
        
        # Guest path should be absolute (Unix-style)
        if not v.startswith('/'):
            raise ValueError("Guest path must be absolute (start with /)")
        
        # Basic path validation
        if '..' in v:
            raise ValueError("Guest path cannot contain '..' references")
        
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "host_path": "./www",
                "guest_path": "/var/www/html",
                "disabled": False,
                "options": {
                    "type": "nfs",
                    "mount_options": ["vers=3", "tcp"]
                }
            }
        }

    def get_vagrant_config(self) -> str:
        """Generate Vagrant configuration string for this synced folder."""
        if self.disabled:
            return f'config.vm.synced_folder "{self.host_path}", "{self.guest_path}", disabled: true'
        
        # Build options string
        options_parts = []
        for key, value in self.options.items():
            if isinstance(value, bool):
                options_parts.append(f"{key}: {str(value).lower()}")
            elif isinstance(value, str):
                options_parts.append(f'{key}: "{value}"')
            elif isinstance(value, list):
                # For arrays like mount_options
                array_str = '[' + ', '.join(f'"{item}"' for item in value) + ']'
                options_parts.append(f"{key}: {array_str}")
            else:
                options_parts.append(f"{key}: {value}")
        
        if options_parts:
            options_str = ", " + ", ".join(options_parts)
        else:
            options_str = ""
        
        return f'config.vm.synced_folder "{self.host_path}", "{self.guest_path}"{options_str}'

    def validate_folder(self) -> tuple[list[str], list[str]]:
        """
        Validate the synced folder configuration.
        
        Returns:
            tuple: (errors, warnings)
        """
        errors = []
        warnings = []

        # Check if host path exists (warning only)
        if not os.path.exists(self.host_path):
            warnings.append(f"Host path does not exist: {self.host_path}")
        
        # Check for common problematic paths
        dangerous_guest_paths = ['/etc', '/bin', '/usr', '/var/log', '/tmp']
        if any(self.guest_path.startswith(path) for path in dangerous_guest_paths):
            warnings.append(f"Guest path may conflict with system directories: {self.guest_path}")

        return errors, warnings