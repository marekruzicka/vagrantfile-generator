"""
Deployment mode utilities.

Provides functions to detect and validate deployment mode from environment variables.
"""

import os
from enum import Enum


class DeploymentMode(str, Enum):
    """Deployment mode enumeration."""
    SELF_HOSTED = "self-hosted"
    PUBLIC = "public"


def get_deployment_mode() -> DeploymentMode:
    """
    Get the current deployment mode from environment variable.
    
    Returns:
        DeploymentMode: The deployment mode (defaults to self-hosted if not set)
    
    Raises:
        ValueError: If the deployment mode is invalid
    """
    mode = os.getenv("DEPLOYMENT_MODE", "self-hosted").lower()
    
    if mode not in [DeploymentMode.SELF_HOSTED, DeploymentMode.PUBLIC]:
        raise ValueError(
            f"Invalid DEPLOYMENT_MODE: {mode}. "
            f"Must be one of: {DeploymentMode.SELF_HOSTED}, {DeploymentMode.PUBLIC}"
        )
    
    return DeploymentMode(mode)


def is_public_mode() -> bool:
    """
    Check if the application is running in public mode.
    
    Returns:
        bool: True if public mode, False otherwise
    """
    return get_deployment_mode() == DeploymentMode.PUBLIC


def is_self_hosted_mode() -> bool:
    """
    Check if the application is running in self-hosted mode.
    
    Returns:
        bool: True if self-hosted mode, False otherwise
    """
    return get_deployment_mode() == DeploymentMode.SELF_HOSTED
