"""
Session Service.

Handles JWT token generation and validation for user sessions.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional
import jwt

from ..models.session_token import SessionToken
from ..models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class SessionService:
    """Service for managing user sessions with JWT tokens."""
    
    def __init__(self):
        """Initialize session service with JWT configuration."""
        self.secret_key = os.getenv("JWT_SECRET")
        self.algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        self.expiration_hours = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        
        if not self.secret_key:
            logger.warning("JWT_SECRET not set - using insecure default. Set JWT_SECRET in production!")
            self.secret_key = "insecure-development-secret-change-in-production"
    
    def create_token(self, user: UserProfile) -> str:
        """
        Create a JWT token for an authenticated user.
        
        Args:
            user: User profile to create token for
            
        Returns:
            str: Encoded JWT token
        """
        now = datetime.utcnow()
        expiration = now + timedelta(hours=self.expiration_hours)
        
        # Create token claims
        claims = SessionToken(
            user_id=user.user_id,
            email=user.email,
            auth_provider=user.auth_provider,
            iat=int(now.timestamp()),
            exp=int(expiration.timestamp())
        )
        
        # Encode JWT token
        token = jwt.encode(
            claims.model_dump(),
            self.secret_key,
            algorithm=self.algorithm
        )
        
        logger.info(f"Created session token for user {user.user_id}, expires at {expiration}")
        return token
    
    def verify_token(self, token: str) -> Optional[SessionToken]:
        """
        Verify and decode a JWT token.
        
        Args:
            token: JWT token string to verify
            
        Returns:
            SessionToken: Decoded token claims if valid, None otherwise
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.algorithm]
            )
            
            # Validate token claims structure
            session_token = SessionToken(**payload)
            
            # Check expiration
            if session_token.is_expired():
                logger.warning(f"Token expired for user {session_token.user_id}")
                return None
            
            return session_token
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            return None
    
    def decode_token_unsafe(self, token: str) -> Optional[dict]:
        """
        Decode a token without verification (for debugging/inspection only).
        
        Args:
            token: JWT token string to decode
            
        Returns:
            dict: Decoded token claims, None if decoding fails
        """
        try:
            return jwt.decode(
                token,
                options={"verify_signature": False}
            )
        except Exception as e:
            logger.error(f"Failed to decode token: {str(e)}")
            return None


# Global session service instance
session_service = SessionService()
