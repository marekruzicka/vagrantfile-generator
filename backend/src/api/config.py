"""
Configuration API endpoints.

Provides public endpoints for retrieving application configuration.
"""

from fastapi import APIRouter
from pydantic import BaseModel

from ..utils.deployment import get_deployment_mode, DeploymentMode


router = APIRouter(prefix="/api/config", tags=["config"])


class DeploymentModeResponse(BaseModel):
    """Deployment mode response model."""
    mode: str


@router.get("/deployment-mode", response_model=DeploymentModeResponse)
async def get_deployment_mode_endpoint():
    """
    Get the current deployment mode.
    
    Returns:
        DeploymentModeResponse: The deployment mode (self-hosted or public)
    """
    mode = get_deployment_mode()
    return DeploymentModeResponse(mode=mode.value)
