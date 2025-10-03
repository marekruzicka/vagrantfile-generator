"""
Global Trigger models for Vagrantfile GUI Generator.

These models represent global Vagrant triggers that can be configured
once in Settings and applied to all VMs in a project.
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class TriggerConfig(BaseModel):
    """Configuration for Vagrant trigger."""
    timing: Literal["before", "after"] = Field(
        ...,
        description="When to execute: before or after the stage"
    )
    stage: str = Field(
        ...,
        description="Vagrant lifecycle stage (up, destroy, halt, resume, provision, reload, etc.)"
    )
    name: Optional[str] = Field(
        default=None,
        description="Trigger identifier (trigger.name in Vagrantfile)"
    )
    info: Optional[str] = Field(
        default=None,
        description="Info message to display (trigger.info)"
    )
    warn: Optional[str] = Field(
        default=None,
        description="Warning message to display (trigger.warn)"
    )
    run: Optional[str] = Field(
        default=None,
        description="Local command to execute on host (mutually exclusive with run_remote)"
    )
    run_remote_inline: Optional[str] = Field(
        default=None,
        description="Remote command to execute in VM (mutually exclusive with run)"
    )
    on_error: Literal["halt", "continue"] = Field(
        default="continue",
        description="Action to take on error: halt or continue"
    )
    
    @field_validator('stage')
    @classmethod
    def validate_stage(cls, v: str) -> str:
        """Validate stage is not empty."""
        if not v or not v.strip():
            raise ValueError("Stage cannot be empty")
        return v.strip()
    
    def model_post_init(self, __context):
        """Validate that either run or run_remote is specified, but not both."""
        if not self.run and not self.run_remote_inline:
            raise ValueError("Either 'run' or 'run_remote_inline' must be specified")
        if self.run and self.run_remote_inline:
            raise ValueError("Cannot specify both 'run' and 'run_remote_inline'")


class GlobalTrigger(BaseModel):
    """Global trigger configuration model."""
    id: str = Field(..., description="Unique identifier for the trigger")
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Trigger name (displayed in UI)"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional description of what the trigger does"
    )
    trigger_config: TriggerConfig = Field(
        ...,
        description="Trigger execution configuration"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when trigger was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when trigger was last updated"
    )
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate trigger name."""
        if not v or not v.strip():
            raise ValueError("Trigger name cannot be empty")
        return v
    
    def _escape_ruby_string(self, s: str) -> str:
        """
        Escape a string for use in Ruby double-quoted strings.
        
        Args:
            s: String to escape
            
        Returns:
            Escaped string safe for Ruby double quotes
        """
        if not s:
            return ""
        # Escape backslashes first, then quotes, then hash symbols for interpolation
        return s.replace('\\', '\\\\').replace('"', '\\"').replace('#{', '\\#{')
    
    def get_vagrant_config(self) -> str:
        """
        Generate Vagrant configuration for this trigger.
        
        Returns:
            Ruby code block for the trigger
        """
        cfg = self.trigger_config
        lines = []
        
        # Add comment header
        lines.append(f"# Trigger: {self.name}")
        if self.description:
            lines.append(f"# {self.description}")
        
        # Start trigger block
        lines.append(f"config.trigger.{cfg.timing} :{cfg.stage} do |trigger|")
        
        # Add trigger properties
        if cfg.name:
            lines.append(f'  trigger.name = "{self._escape_ruby_string(cfg.name)}"')
        
        if cfg.info:
            lines.append(f'  trigger.info = "{self._escape_ruby_string(cfg.info)}"')
        
        if cfg.warn:
            lines.append(f'  trigger.warn = "{self._escape_ruby_string(cfg.warn)}"')
        
        # Add execution command
        if cfg.run:
            # For multi-line or complex commands, use heredoc
            if '\n' in cfg.run or len(cfg.run) > 80:
                lines.append('  trigger.run = { inline: <<-SHELL')
                lines.append(f'    {cfg.run}')
                lines.append('  SHELL')
                lines.append('  }')
            else:
                lines.append(f'  trigger.run = {{ inline: "{self._escape_ruby_string(cfg.run)}" }}')
        elif cfg.run_remote_inline:
            # For multi-line or complex commands, use heredoc
            if '\n' in cfg.run_remote_inline or len(cfg.run_remote_inline) > 80:
                lines.append('  trigger.run_remote = { inline: <<-SHELL')
                lines.append(f'    {cfg.run_remote_inline}')
                lines.append('  SHELL')
                lines.append('  }')
            else:
                lines.append(f'  trigger.run_remote = {{ inline: "{self._escape_ruby_string(cfg.run_remote_inline)}" }}')
        
        # Add error handling
        lines.append(f"  trigger.on_error = :{cfg.on_error}")
        
        # Close block
        lines.append("end")
        
        return "\n".join(lines)


class GlobalTriggerCreate(BaseModel):
    """Schema for creating a new global trigger."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Trigger name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional trigger description"
    )
    trigger_config: TriggerConfig = Field(
        ...,
        description="Trigger execution configuration"
    )


class GlobalTriggerUpdate(BaseModel):
    """Schema for updating an existing global trigger."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Trigger name"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional trigger description"
    )
    trigger_config: TriggerConfig = Field(
        ...,
        description="Trigger execution configuration"
    )


class GlobalTriggerSummary(BaseModel):
    """Summary model for listing triggers."""
    id: str
    name: str
    description: Optional[str]
    timing: str
    stage: str
    created_at: datetime
    updated_at: datetime
