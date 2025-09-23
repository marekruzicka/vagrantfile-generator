"""
Provisioner model for Vagrantfile GUI Generator.

This module defines provisioner configurations for setting up and configuring
virtual machines with scripts and configuration management tools.
"""

from typing import List, Optional, Dict, Any
from enum import Enum
import os

from pydantic import BaseModel, Field, field_validator, ValidationInfo, model_validator


class ProvisionerType(str, Enum):
    """Supported provisioner types."""
    SHELL = "shell"
    ANSIBLE = "ansible"
    PUPPET = "puppet"
    CHEF = "chef"


class Provisioner(BaseModel):
    """Provisioner configuration model."""
    
    type: ProvisionerType = Field(
        ...,
        description="Type of provisioner"
    )
    script_path: Optional[str] = Field(
        default=None,
        description="Path to script file (for shell type)"
    )
    inline: Optional[str] = Field(
        default=None,
        description="Inline script content (for shell type)"
    )
    args: List[str] = Field(
        default_factory=list,
        description="Script arguments"
    )
    privileged: bool = Field(
        default=True,
        description="Run with sudo (for shell type)"
    )
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Provisioner-specific configuration"
    )

    @field_validator('script_path')
    @classmethod
    def validate_script_path(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate script path for shell provisioners."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        # For shell provisioners, either script_path or inline is required
        if info.data.get('type') == ProvisionerType.SHELL:
            # Path should exist (warning in validation method)
            pass
        
        return v

    @field_validator('inline')
    @classmethod
    def validate_inline(cls, v: Optional[str], info: ValidationInfo) -> Optional[str]:
        """Validate inline script content."""
        if v is None:
            return v
        
        v = v.strip()
        if not v:
            return None
        
        return v

    @model_validator(mode='after')
    def validate_provisioner(self) -> 'Provisioner':
        """Cross-field validation."""
        if self.type == ProvisionerType.SHELL:
            if not self.script_path and not self.inline:
                raise ValueError("Shell provisioner requires either script_path or inline content")
            if self.script_path and self.inline:
                raise ValueError("Shell provisioner cannot have both script_path and inline content")
        return self

    model_config = {
        "json_schema_extra": {
            "example": {
                "type": "shell",
                "script_path": "scripts/bootstrap.sh",
                "args": ["--verbose"],
                "privileged": True
            }
        }
    }

    def get_vagrant_config(self) -> str:
        """Generate Vagrant configuration string for this provisioner."""
        config_lines = []
        
        if self.type == ProvisionerType.SHELL:
            if self.script_path:
                config_lines.append(f'path: "{self.script_path}"')
            elif self.inline:
                # Escape the inline script properly
                escaped_script = self.inline.replace('"', '\\"').replace('\n', '\\n')
                config_lines.append(f'inline: "{escaped_script}"')
            
            if self.args:
                args_str = ', '.join(f'"{arg}"' for arg in self.args)
                config_lines.append(f'args: [{args_str}]')
            
            config_lines.append(f'privileged: {str(self.privileged).lower()}')
        
        else:
            # For other provisioner types, use the config dict
            for key, value in self.config.items():
                if isinstance(value, bool):
                    config_lines.append(f'{key}: {str(value).lower()}')
                elif isinstance(value, str):
                    config_lines.append(f'{key}: "{value}"')
                else:
                    config_lines.append(f'{key}: {value}')
        
        config_str = ', '.join(config_lines)
        return f'config.vm.provision "{self.type}", {config_str}'

    def validate_provisioner(self) -> tuple[list[str], list[str]]:
        """
        Validate the provisioner configuration.
        
        Returns:
            tuple: (errors, warnings)
        """
        errors = []
        warnings = []

        if self.type == ProvisionerType.SHELL:
            if not self.script_path and not self.inline:
                errors.append("Shell provisioner requires either script_path or inline content")
            
            if self.script_path:
                if not os.path.exists(self.script_path):
                    warnings.append(f"Script file does not exist: {self.script_path}")
                elif not os.access(self.script_path, os.R_OK):
                    warnings.append(f"Script file is not readable: {self.script_path}")
            
            if self.inline and len(self.inline) > 1000:
                warnings.append("Inline script is very long, consider using a script file")

        return errors, warnings