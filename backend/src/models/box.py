"""
Box model for Vagrantfile GUI Generator.

This module defines the Box data model for storing and managing
Vagrant box configurations.
"""

from typing import Optional
from pydantic import BaseModel, Field


class Box(BaseModel):
    """Represents a Vagrant box configuration."""
    
    id: str = Field(..., description="Unique identifier for the box")
    name: str = Field(..., description="Box name (e.g., 'generic/ubuntu2204')")
    description: str = Field(..., description="Human-readable description")
    provider: str = Field(default="libvirt", description="Vagrant provider (libvirt, virtualbox, etc.)")
    version: Optional[str] = Field(default=None, description="Box version constraint")
    url: Optional[str] = Field(default=None, description="Custom box URL")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            # Add any custom encoders if needed
        }
        
    def __str__(self) -> str:
        """String representation of the box."""
        return f"Box(name='{self.name}', provider='{self.provider}')"
        
    def __repr__(self) -> str:
        """Detailed string representation of the box."""
        return self.__str__()


class BoxCreate(BaseModel):
    """Model for creating a new box."""
    
    name: str = Field(..., description="Box name (e.g., 'generic/ubuntu2204')")
    description: str = Field(..., description="Human-readable description")
    provider: str = Field(default="libvirt", description="Vagrant provider")
    version: Optional[str] = Field(default=None, description="Box version constraint")
    url: Optional[str] = Field(default=None, description="Custom box URL")


class BoxUpdate(BaseModel):
    """Model for updating an existing box."""
    
    name: Optional[str] = Field(default=None, description="Box name")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    provider: Optional[str] = Field(default=None, description="Vagrant provider")
    version: Optional[str] = Field(default=None, description="Box version constraint")
    url: Optional[str] = Field(default=None, description="Custom box URL")


class BoxSummary(BaseModel):
    """Summary model for box listing."""
    
    id: str = Field(..., description="Unique identifier for the box")
    name: str = Field(..., description="Box name")
    description: str = Field(..., description="Human-readable description")
    provider: str = Field(..., description="Vagrant provider")
    
    class Config:
        """Pydantic configuration."""
        from_attributes = True