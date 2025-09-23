"""
API endpoints package for Vagrantfile GUI Generator.

This package contains all FastAPI routers for the application.
"""

from .projects import router as projects_router
from .vms import router as vms_router
from .generation import router as generation_router

__all__ = [
    "projects_router",
    "vms_router", 
    "generation_router"
]