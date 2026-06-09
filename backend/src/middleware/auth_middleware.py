"""
Authentication Middleware.

Provides FastAPI dependency for validating JWT tokens and extracting current user.
"""

import logging
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, Header, status

from ..models.user_profile import UserProfile
from ..services.session_service import session_service
from ..utils.deployment import is_public_mode, is_self_hosted_mode

logger = logging.getLogger(__name__)


async def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None
) -> Optional[UserProfile]:
    """
    FastAPI dependency to get the current authenticated user.
    
    In self-hosted mode, returns None (no authentication required).
    In public mode, validates JWT token and returns user profile.
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        Optional[UserProfile]: User profile if authenticated, None in self-hosted mode
        
    Raises:
        HTTPException: 401 if authentication required but token is missing/invalid
    """
    # In self-hosted mode, no authentication required
    if is_self_hosted_mode():
        return None
    
    # In public mode, authentication is required
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = parts[1]
    
    # Verify token
    session_token = session_service.verify_token(token)
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Return user profile from token claims
    # Note: In a full implementation, we might fetch the full user profile from storage
    # For now, we construct it from token claims
    from datetime import datetime
    user_profile = UserProfile(
        user_id=session_token.user_id,
        email=session_token.email,
        name=None,  # Not stored in token
        auth_provider=session_token.auth_provider,
        created_at=datetime.fromtimestamp(session_token.iat),
        last_login=datetime.fromtimestamp(session_token.iat)
    )
    
    return user_profile


async def get_optional_user(
    authorization: Annotated[Optional[str], Header()] = None
) -> Optional[UserProfile]:
    """
    FastAPI dependency to optionally get the current user.
    
    Similar to get_current_user but doesn't raise an exception if no token is provided.
    Used for endpoints that work in both self-hosted and public modes.
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        Optional[UserProfile]: User profile if authenticated, None otherwise
    """
    try:
        return await get_current_user(authorization)
    except HTTPException:
        return None
