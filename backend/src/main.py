"""
Main FastAPI application for Vagrantfile GUI Generator.

This module sets up the FastAPI application with all routes and middleware.
"""

import os
from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .api import projects_router, vms_router, generation_router
from .api.boxes import router as boxes_router
from .api.footer import router as footer_router
from .api.plugins import router as plugins_router
from .services import ProjectNotFoundError

# Get environment variables for configuration
def get_cors_origins() -> List[str]:
    """Get CORS origins from environment variable."""
    cors_origins = os.getenv("CORS_ORIGINS", "")
    if cors_origins and cors_origins.strip() != "":
        return [origin.strip() for origin in cors_origins.split(",")]
    else:
        # Default to localhost in development if not specified or empty
        return ["http://localhost:5173"]

# Create FastAPI application
app = FastAPI(
    title="Vagrantfile GUI Generator API",
    description="API for generating Vagrantfiles through a web interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = get_cors_origins()
print(f"CORS Origins: {cors_origins}")

# Add CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(projects_router, prefix="/api", tags=["projects"])
app.include_router(vms_router, prefix="/api", tags=["vms"])
app.include_router(generation_router, prefix="/api", tags=["generation"])
app.include_router(boxes_router, prefix="/api", tags=["boxes"])
app.include_router(footer_router, prefix="/api", tags=["footer"])
app.include_router(plugins_router, prefix="/api", tags=["plugins"])

# Global exception handlers
@app.exception_handler(ProjectNotFoundError)
async def project_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"error": str(exc)}
    )

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"error": str(exc)}
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "vagrantfile-gui-api"}

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Vagrantfile GUI Generator API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Serve static frontend files (if directory exists)
try:
    import os
    frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "src")
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
except Exception:
    # Frontend directory doesn't exist yet, skip static file serving
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)