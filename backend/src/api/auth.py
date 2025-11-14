"""
Authentication API endpoints.

Handles OTP and OIDC authentication flows.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from ..models.user_profile import UserProfile
from ..services.otp_service import otp_service
from ..services.rate_limit_service import rate_limit_service
from ..services.user_service import user_service
from ..services.email_service import email_service
from ..services.session_service import session_service
from ..middleware.auth_middleware import get_current_user
from ..utils.validators import validate_email, validate_otp_code

router = APIRouter(prefix="/api/auth", tags=["authentication"])


class OTPRequestBody(BaseModel):
    """Request body for OTP request."""
    email: str = Field(..., description="Email address to send OTP to")


class OTPRequestResponse(BaseModel):
    """Response for OTP request."""
    message: str
    email: str
    expires_in_minutes: int


class OTPVerifyBody(BaseModel):
    """Request body for OTP verification."""
    email: str = Field(..., description="Email address")
    code: str = Field(..., description="6-digit OTP code")


class AuthResponse(BaseModel):
    """Response for successful authentication."""
    token: str = Field(..., description="JWT session token")
    user: UserProfile = Field(..., description="User profile")


class LogoutResponse(BaseModel):
    """Response for logout."""
    message: str


@router.post("/otp/request", response_model=OTPRequestResponse)
async def request_otp(body: OTPRequestBody):
    """
    Request an OTP code via email.
    
    Rate limited to prevent abuse (5 requests per hour by default).
    """
    # Validate email
    if not validate_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address"
        )
    
    # Check if email service is configured
    if not email_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured. OTP authentication is disabled."
        )
    
    # Check rate limit
    if rate_limit_service.check_rate_limit(body.email):
        remaining = rate_limit_service.get_remaining_requests(body.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again later. Remaining requests: {remaining}"
        )
    
    # Generate OTP
    otp_request = otp_service.generate_otp(body.email)
    
    # Store OTP
    otp_service.store_otp(otp_request)
    
    # Record request for rate limiting
    rate_limit_service.record_request(body.email)
    
    # Send email
    try:
        email_service.send_otp_email(body.email, otp_request.code)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP email: {str(e)}"
        )
    
    return OTPRequestResponse(
        message="OTP code sent to your email",
        email=body.email,
        expires_in_minutes=int(otp_service.expiration_minutes)
    )


@router.post("/otp/verify", response_model=AuthResponse)
async def verify_otp(body: OTPVerifyBody):
    """
    Verify OTP code and create session.
    
    Returns JWT token and user profile on success.
    """
    # Validate inputs
    if not validate_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email address"
        )
    
    if not validate_otp_code(body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code format. Must be 6 digits."
        )
    
    # Verify OTP
    if not otp_service.verify_otp(body.email, body.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP code"
        )
    
    # Create or update user
    user = user_service.create_or_update_user(
        email=body.email,
        auth_provider="email"
    )
    
    # Generate JWT token
    token = session_service.create_token(user)
    
    return AuthResponse(
        token=token,
        user=user
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    
    Requires valid JWT token in Authorization header.
    """
    # Update last login
    user_service.update_last_login(current_user.user_id)
    
    return current_user


@router.post("/logout", response_model=LogoutResponse)
async def logout(current_user: Optional[UserProfile] = Depends(get_current_user)):
    """
    Logout current user.
    
    Client should remove the JWT token from local storage.
    Server-side session invalidation is not implemented (stateless JWT).
    """
    return LogoutResponse(
        message="Logged out successfully. Please remove your token from local storage."
    )
