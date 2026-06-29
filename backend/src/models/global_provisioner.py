"""
Global Provisioner models for Vagrantfile Generator.

These models represent global Vagrant provisioners that can be configured
once in Settings and applied to all VMs in a project.
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator

from ..utils.ansible import render_ansible_block


class ShellProvisionerConfig(BaseModel):
    """Configuration for shell provisioner."""
    script: str = Field(
        ...,
        min_length=1,
        description="Shell script to execute (heredoc syntax will be used)"
    )
    privileged: bool = Field(
        default=True,
        description="Whether to run the script with sudo privileges"
    )
    run: Literal["once", "always", "never"] = Field(
        default="once",
        description="When to run the provisioner: once (default), always, or never"
    )
    path: Optional[str] = Field(
        default=None,
        description="Path to external script file (alternative to inline script)"
    )
    
    @field_validator('script')
    @classmethod
    def validate_script(cls, v: str) -> str:
        """Validate script is not empty."""
        if not v or not v.strip():
            raise ValueError("Script cannot be empty")
        return v


class AnsibleProvisionerConfig(BaseModel):
    """Configuration for ansible provisioner."""
    playbook: str = Field(..., min_length=1, description="Path to Ansible playbook")
    extra_vars: Optional[str] = Field(default=None, description="Extra variables in YAML format")
    tags: Optional[str] = Field(default=None, description="Tags to run")
    skip_tags: Optional[str] = Field(default=None, description="Tags to skip")
    verbose: Literal["off", "v", "vv", "vvv", "vvvv"] = Field(default="off")
    raw_args: Optional[str] = Field(default=None, description="Raw additional arguments")

    @field_validator('playbook')
    @classmethod
    def validate_playbook(cls, v: str) -> str:
        """Validate playbook path is not empty."""
        if not v or not v.strip():
            raise ValueError("Playbook path cannot be empty")
        return v

    @field_validator('extra_vars')
    @classmethod
    def validate_extra_vars(cls, v: Optional[str]) -> Optional[str]:
        """Validate extra_vars is a YAML dictionary when provided."""
        if v is None or not v.strip():
            return None
        import yaml
        try:
            parsed = yaml.safe_load(v)
            if not isinstance(parsed, dict):
                raise ValueError("extra_vars must be a YAML dictionary (key-value pairs)")
        except yaml.YAMLError as e:
            raise ValueError(f"extra_vars is not valid YAML: {e}")
        return v


class GlobalProvisioner(BaseModel):
    """Global provisioner configuration model."""
    id: str = Field(..., description="Unique identifier for the provisioner")
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Provisioner name (used in Vagrantfile comments)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description of what the provisioner does"
    )
    type: Literal["shell", "ansible"] = Field(
        default="shell",
        description="Provisioner type"
    )
    scope: Literal["global"] = Field(
        default="global",
        description="Provisioner scope (currently only global supported)"
    )
    shell_config: Optional[ShellProvisionerConfig] = Field(
        default=None,
        description="Shell provisioner configuration"
    )
    ansible_config: Optional[AnsibleProvisionerConfig] = Field(
        default=None,
        description="Ansible provisioner configuration"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when provisioner was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when provisioner was last updated"
    )
    is_shared: Optional[bool] = Field(
        default=False,
        description="Whether this is a shared resource"
    )
    owner_id: Optional[str] = Field(
        default=None,
        description="User ID of the owner (None for shared)"
    )
    source_id: Optional[str] = Field(
        default=None,
        description="ID of the original shared resource this was copied from"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate provisioner name."""
        if not v or not v.strip():
            raise ValueError("Provisioner name cannot be empty")
        return v

    @model_validator(mode='after')
    def validate_config(self) -> 'GlobalProvisioner':
        """Validate provisioner config matches its type."""
        if self.type == "shell":
            if not self.shell_config:
                raise ValueError("Shell provisioner requires shell_config")
            if self.ansible_config is not None:
                raise ValueError("Shell provisioner cannot have ansible_config")
        if self.type == "ansible":
            if not self.ansible_config:
                raise ValueError("Ansible provisioner requires ansible_config")
            if self.shell_config is not None:
                raise ValueError("Ansible provisioner cannot have shell_config")
        return self
    
    def get_variable_name(self) -> str:
        """
        Get a safe Ruby variable name based on the provisioner name.
        
        Returns:
            Ruby-safe variable name
        """
        # Convert name to lowercase and replace non-alphanumeric with underscore
        cleaned = ''.join(c if c.isalnum() or c == '_' else '_' for c in self.name.lower())
        return f"provisioner_{cleaned}_script"
    
    def get_vagrant_config(self) -> str:
        """
        Generate Vagrant configuration for this provisioner.
        
        Returns:
            Ruby code for Vagrantfile
        """
        if self.type == "shell" and self.shell_config:
            lines = []
            
            # Add comment
            lines.append(f"# Shell provisioner: {self.name}")
            if self.description:
                lines.append(f"# {self.description}")
            
            # If using path, don't need variable
            if self.shell_config.path:
                provision_args = [f'"shell", path: "{self.shell_config.path}"']
                
                if not self.shell_config.privileged:
                    provision_args.append('privileged: false')
                
                if self.shell_config.run != "once":
                    provision_args.append(f'run: "{self.shell_config.run}"')
                
                lines.append(f"config.vm.provision {', '.join(provision_args)}")
            else:
                # Define script variable
                var_name = self.get_variable_name()
                lines.append(f"${var_name} = <<-SCRIPT")
                lines.append(self.shell_config.script)
                lines.append("SCRIPT")
                lines.append("")
                
                # Provisioner configuration
                provision_args = [f'"shell", inline: ${var_name}']
                
                if not self.shell_config.privileged:
                    provision_args.append('privileged: false')
                
                if self.shell_config.run != "once":
                    provision_args.append(f'run: "{self.shell_config.run}"')
                
                lines.append(f"config.vm.provision {', '.join(provision_args)}")
            
            return '\n'.join(lines)
        elif self.type == "ansible" and self.ansible_config:
            lines = []
            lines.append(f"# Ansible provisioner: {self.name}")
            if self.description:
                lines.append(f"# {self.description}")

            config_dict = self.ansible_config.model_dump()
            if config_dict.get("extra_vars"):
                import yaml
                config_dict["extra_vars"] = yaml.safe_load(config_dict["extra_vars"])

            lines.append(render_ansible_block(config_dict))
            return '\n'.join(lines)
        
        return ""


class GlobalProvisionerCreate(BaseModel):
    """Model for creating a new global provisioner."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    type: Literal["shell", "ansible"] = Field(default="shell")
    scope: Literal["global"] = Field(default="global")
    shell_config: Optional[ShellProvisionerConfig] = None
    ansible_config: Optional[AnsibleProvisionerConfig] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate provisioner name."""
        if not v or not v.strip():
            raise ValueError("Provisioner name cannot be empty")
        return v

    @model_validator(mode='after')
    def validate_config(self) -> 'GlobalProvisionerCreate':
        """Validate provisioner config matches its type."""
        if self.type == "shell":
            if not self.shell_config:
                raise ValueError("Shell provisioner requires shell_config")
            if self.ansible_config is not None:
                raise ValueError("Shell provisioner cannot have ansible_config")
        if self.type == "ansible":
            if not self.ansible_config:
                raise ValueError("Ansible provisioner requires ansible_config")
            if self.shell_config is not None:
                raise ValueError("Ansible provisioner cannot have shell_config")
        return self


class GlobalProvisionerUpdate(BaseModel):
    """Model for updating an existing global provisioner."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    shell_config: Optional[ShellProvisionerConfig] = None
    ansible_config: Optional[AnsibleProvisionerConfig] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate provisioner name if provided."""
        if v is not None and (not v or not v.strip()):
            raise ValueError("Provisioner name cannot be empty")
        return v


class GlobalProvisionerSummary(BaseModel):
    """Global provisioner summary for list views."""
    id: str
    name: str
    description: Optional[str] = None
    type: Literal["shell", "ansible"] = "shell"
    scope: Literal["global"] = "global"
    is_shared: Optional[bool] = False
    owner_id: Optional[str] = None
