"""
Plugin model for Vagrantfile GUI Generator.

This module defines the Plugin data model for storing and managing
Vagrant plugin configurations.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Plugin(BaseModel):
    """Represents a Vagrant plugin configuration."""
    
    id: str = Field(..., description="Unique identifier for the plugin")
    name: str = Field(..., description="Plugin name (e.g., 'vagrant-vbguest')")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    source_url: Optional[str] = Field(default=None, description="Source code repository URL")
    documentation_url: Optional[str] = Field(default=None, description="Documentation URL")
    default_version: Optional[str] = Field(default=None, description="Default version constraint")
    configuration: Optional[str] = Field(default=None, description="Plugin-specific configuration (Ruby code)")
    is_deprecated: bool = Field(default=False, description="Whether the plugin is deprecated")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Add any custom encoders if needed
        }
        
    def __str__(self) -> str:
        """String representation of the plugin."""
        status = " (deprecated)" if self.is_deprecated else ""
        return f"Plugin(name='{self.name}'{status})"
        
    def __repr__(self) -> str:
        """Detailed string representation of the plugin."""
        return self.__str__()


class PluginCreate(BaseModel):
    """Model for creating a new plugin."""
    
    name: str = Field(..., description="Plugin name (e.g., 'vagrant-vbguest')")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    source_url: Optional[str] = Field(default=None, description="Source code repository URL")
    documentation_url: Optional[str] = Field(default=None, description="Documentation URL")
    default_version: Optional[str] = Field(default=None, description="Default version constraint")
    configuration: Optional[str] = Field(default=None, description="Plugin-specific configuration (Ruby code)")
    is_deprecated: bool = Field(default=False, description="Whether the plugin is deprecated")


class PluginUpdate(BaseModel):
    """Model for updating an existing plugin."""
    
    name: Optional[str] = Field(default=None, description="Plugin name")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    source_url: Optional[str] = Field(default=None, description="Source code repository URL")
    documentation_url: Optional[str] = Field(default=None, description="Documentation URL")
    default_version: Optional[str] = Field(default=None, description="Default version constraint")
    configuration: Optional[str] = Field(default=None, description="Plugin-specific configuration (Ruby code)")
    is_deprecated: Optional[bool] = Field(default=None, description="Whether the plugin is deprecated")


class PluginSummary(BaseModel):
    """Summary model for plugin listing."""
    
    id: str = Field(..., description="Unique identifier for the plugin")
    name: str = Field(..., description="Plugin name")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    default_version: Optional[str] = Field(default=None, description="Default version constraint")
    is_deprecated: bool = Field(default=False, description="Whether the plugin is deprecated")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True
