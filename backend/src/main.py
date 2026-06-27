"""
Main FastAPI application for Vagrantfile Generator.

This module sets up the FastAPI application with all routes and middleware.
"""

import logging
import sys
import os
import json
from pathlib import Path
from typing import List, Optional, TextIO
import time
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .api import projects_router, vms_router, generation_router
from .api.boxes import router as boxes_router
from .api.footer import router as footer_router
from .api.plugins import router as plugins_router
from .api.project_plugins import router as project_plugins_router
from .api.provisioners import router as provisioners_router
from .api.project_provisioners import router as project_provisioners_router
from .api.triggers import router as triggers_router
from .api.project_triggers import router as project_triggers_router
from .api.config import router as config_router
from .api.auth import router as auth_router
from .services import ProjectNotFoundError
from .utils.deployment import get_deployment_mode, DeploymentMode

try:
    from uvicorn.logging import AccessFormatter

    _original_access_format = AccessFormatter.formatMessage

    def _safe_access_format(self, record):
        try:
            return _original_access_format(self, record)
        except ValueError:
            return record.getMessage()

    if not getattr(AccessFormatter, "_safe_format_applied", False):
        AccessFormatter.formatMessage = _safe_access_format
        AccessFormatter._safe_format_applied = True
except ImportError:
    pass


# Configure access logger for custom reports
class RequestLogger:
    """Lightweight logger that writes request summaries directly to stdout."""

    def __init__(self, stream: TextIO | None = None):
        self._stream = stream or sys.stdout

    def info(self, message: str, *args, **kwargs) -> None:
        """Log an info message, formatting with args if provided."""
        if args:
            try:
                formatted_message = message % args
            except (TypeError, ValueError):
                formatted_message = f"{message} {args}"
        else:
            formatted_message = message

        self._stream.write(f"{formatted_message}\n")
        self._stream.flush()


REQUEST_LOGGER = RequestLogger()

# Silence uvicorn.access logger to avoid AccessFormatter ValueErrors
UVICORN_ACCESS_LOGGER = logging.getLogger("uvicorn.access")
UVICORN_ACCESS_LOGGER.handlers.clear()
UVICORN_ACCESS_LOGGER.propagate = False
UVICORN_ACCESS_LOGGER.disabled = True


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
    title="Vagrantfile Generator API",
    description="API for generating Vagrantfiles through a web interface",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


# Resolve frontend version from package.json at startup.
# Graceful fallback if the file is missing or unparseable.
_FRONTEND_VERSION: str = "unknown"
try:
    _pkg_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "package.json"
    with open(_pkg_path, "r", encoding="utf-8") as _f:
        _pkg_data = json.load(_f)
        _FRONTEND_VERSION = _pkg_data.get("version", "unknown")
except Exception:
    pass  # Keep "unknown"


# Startup validation
@app.on_event("startup")
async def startup_validation():
    """Validate configuration on startup."""
    import asyncio
    from .services.cleanup import periodic_cleanup_task

    logger = logging.getLogger("uvicorn")

    # Check deployment mode
    try:
        mode = get_deployment_mode()
        logger.info(f"Deployment mode: {mode.value}")
    except ValueError as e:
        logger.error(f"Invalid deployment mode: {e}")
        raise

    # Validate Mailgun configuration in public mode
    if mode == DeploymentMode.PUBLIC:
        mailgun_api_key = os.getenv("MAILGUN_API_KEY")
        mailgun_domain = os.getenv("MAILGUN_DOMAIN")

        if not mailgun_api_key or not mailgun_domain:
            logger.warning(
                "MAILGUN_API_KEY or MAILGUN_DOMAIN not configured. "
                "Email OTP authentication will be disabled. "
                "Only OIDC authentication will be available in public mode."
            )
        else:
            logger.info(
                "Mailgun configuration detected - Email OTP authentication enabled"
            )

    # Start background cleanup task
    logger.info("Starting background cleanup task (runs every 5 minutes)...")
    asyncio.create_task(periodic_cleanup_task(interval_seconds=300))

    logger.info("Startup validation complete")


# Configure CORS
cors_origins = get_cors_origins()
print(f"CORS Origins: {cors_origins}")


# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all API requests with timing and user info."""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Extract user_id from Authorization header if present
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header:
            try:
                from .services.session_service import session_service

                parts = auth_header.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    token = parts[1]
                    session_token = session_service.verify_token(token)
                    if session_token:
                        user_id = session_token.user_id
            except Exception:
                pass  # Failed to extract user_id, continue without it

        # Process request
        response = await call_next(request)

        # Calculate response time
        process_time = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Log request
        user_info = f"user={user_id}" if user_id else "unauthenticated"
        REQUEST_LOGGER.info(
            "%s %s status=%s %s time=%.2fms",
            request.method,
            request.url.path,
            response.status_code,
            user_info,
            process_time,
        )

        return response


# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add session middleware for OAuth state management
# Uses a dedicated cookie-signing secret, separate from JWT token signing.
session_secret = os.getenv(
    "SESSION_COOKIE_SECRET", "dev-session-cookie-secret-change-in-production"
)
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="oauth_session",
    max_age=600,  # 10 minutes, enough for OAuth flow
    same_site="lax",
    https_only=False,  # Set to True in production with HTTPS
)

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
app.include_router(project_plugins_router, prefix="/api", tags=["project-plugins"])
app.include_router(provisioners_router, prefix="/api", tags=["provisioners"])
app.include_router(
    project_provisioners_router, prefix="/api", tags=["project-provisioners"]
)
app.include_router(triggers_router, prefix="/api", tags=["triggers"])
app.include_router(project_triggers_router, prefix="/api", tags=["project-triggers"])
app.include_router(config_router, tags=["config"])
app.include_router(auth_router, tags=["authentication"])

# Global exception handlers


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent JSON format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "error": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with field-level details."""
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": " -> ".join(str(loc) for loc in error["loc"]),
                "message": error["msg"],
                "type": error["type"],
            }
        )

    return JSONResponse(
        status_code=422,
        content={"status": "error", "error": "Validation error", "details": errors},
    )


@app.exception_handler(ProjectNotFoundError)
async def project_not_found_handler(request: Request, exc: ProjectNotFoundError):
    """Handle project not found errors."""
    return JSONResponse(status_code=404, content={"status": "error", "error": str(exc)})


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle value errors."""
    return JSONResponse(status_code=400, content={"status": "error", "error": str(exc)})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions with a generic error message."""
    import logging

    logger = logging.getLogger("uvicorn.error")

    # Log the actual exception for debugging
    logger.exception(f"Unhandled exception: {exc}")

    # Return generic error to client (don't expose internal details)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "error": "An internal server error occurred. Please try again later.",
        },
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
    return {"message": "Vagrantfile Generator API", "version": "1.0.0", "docs": "/docs"}


# Version endpoint (no auth required)
@app.get("/api/version")
async def api_version():
    """Return backend and frontend version information."""
    return {"backend": app.version, "frontend": _FRONTEND_VERSION}


# Serve static frontend files (if directory exists)
try:
    import os

    frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "frontend", "src"
    )
    if os.path.exists(frontend_path):
        app.mount("/static", StaticFiles(directory=frontend_path), name="static")
except Exception:
    # Frontend directory doesn't exist yet, skip static file serving
    pass

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
