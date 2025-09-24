"""
PluginConfiguration model for Vagrantfile GUI Generator.

This module defines Vagrant plugin configurations that can be applied
globally to a project or specifically to individual VMs.
"""

from typing import Dict, Any, Optional
from enum import Enum
import re

from pydantic import BaseModel, Field, field_validator


class PluginScope(str, Enum):
    """Scope where the plugin configuration applies."""
    GLOBAL = "global"
    VM = "vm"


class PluginConfiguration(BaseModel):
    """Vagrant plugin configuration model."""
    
    name: str = Field(
        ...,
        min_length=1,
        description="Plugin name (e.g., 'vagrant-vbguest')"
    )
    version: Optional[str] = Field(
        default=None,
        description="Plugin version constraint (optional)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Plugin-specific configuration parameters"
    )
    scope: PluginScope = Field(
        default=PluginScope.VM,
        description="Whether applied globally or per-VM"
    )

    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate plugin name follows Vagrant conventions."""
        if not v or not v.strip():
            raise ValueError("Plugin name cannot be empty")
        
        v = v.strip()
        
        # Basic plugin name validation (typically vagrant-something)
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Plugin name can only contain letters, numbers, underscores, and hyphens")
        
        return v

    @field_validator('version')
    @classmethod
    def validate_version(cls, v: Optional[str]) -> Optional[str]:
        """Validate version constraint format if provided."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # Basic semver pattern validation
        semver_pattern = r'^[~^><=]*\d+(\.\d+)*(\.\d+)*(-[\w.]+)?(\+[\w.]+)?$'
        if not re.match(semver_pattern, v):
            raise ValueError("Version must be a valid semantic version constraint")
        
        return v

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "name": "vagrant-vbguest",
                "version": "~> 0.30.0",
                "config": {
                    "auto_update": False,
                    "no_remote": True
                },
                "scope": "vm"
            }
        }

    def get_vagrant_config(self) -> str:
        """Generate Vagrant configuration string for this plugin."""
        config_lines = []
        
        if self.config:
            for key, value in self.config.items():
                if isinstance(value, bool):
                    config_lines.append(f"  {key} = {str(value).lower()}")
                elif isinstance(value, str):
                    config_lines.append(f'  {key} = "{value}"')
                else:
                    config_lines.append(f"  {key} = {value}")
        
        if config_lines:
            config_block = '\n'.join(config_lines)
            return f"config.{self.name} do |plugin|\n{config_block}\nend"
        else:
            return f"# Plugin {self.name} enabled"