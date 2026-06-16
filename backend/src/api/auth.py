"""
Authentication API endpoints.

Handles OTP and OIDC authentication flows.
"""

import os
from typing import Optional
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pydantic import BaseModel, Field

from ..models.user_profile import UserProfile
from ..services.otp_service import otp_service
from ..services.rate_limit_service import rate_limit_service
from ..services.user_service import user_service
from ..services.email_service import email_service
from ..services.session_service import session_service
from ..services.oidc_service import OIDCService, OIDCServiceError
from ..middleware.auth_middleware import get_current_user
from ..utils.validators import validate_email, validate_otp_code

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["authentication"])

# Initialize OIDC service
oidc_service = OIDCService()


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
    Test user (when enabled) bypasses rate limiting and email sending.
    """
    # Validate email
    if not validate_email(body.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address"
        )

    # Check if this is the test user
    is_test_user = otp_service.is_test_user(body.email)

    # Check if email service is configured (not required for test user)
    if not is_test_user and not email_service.is_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured. OTP authentication is disabled.",
        )

    # Check rate limit (skip for test user)
    if not is_test_user and rate_limit_service.check_rate_limit(body.email):
        remaining = rate_limit_service.get_remaining_requests(body.email)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please try again later. Remaining requests: {remaining}",
        )

    # Generate OTP
    otp_request = otp_service.generate_otp(body.email)

    # Store OTP
    otp_service.store_otp(otp_request)

    # Record request for rate limiting (skip for test user)
    if not is_test_user:
        rate_limit_service.record_request(body.email)

    # Send email (skip for test user)
    if not is_test_user:
        try:
            email_service.send_otp_email(body.email, otp_request.code)
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send OTP email: {str(e)}",
            )

    return OTPRequestResponse(
        message=(
            "OTP code sent to your email"
            if not is_test_user
            else "Test user: use static OTP code"
        ),
        email=body.email,
        expires_in_minutes=int(otp_service.expiration_minutes),
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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email address"
        )

    if not validate_otp_code(body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code format. Must be 6 digits.",
        )

    # Verify OTP
    if not otp_service.verify_otp(body.email, body.code):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired OTP code",
        )

    # Create or update user
    user = user_service.create_or_update_user(email=body.email, auth_provider="email")

    # Generate JWT token
    token = session_service.create_token(user)

    return AuthResponse(token=token, user=user)


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    Get current authenticated user's profile.

    Requires valid JWT token in Authorization header.
    """
    # Update last login
    user_service.update_last_login(current_user.user_id)

    return current_user


@router.get("/oidc/{provider}")
async def oidc_login(provider: str, request: Request):
    """
    Initiate OIDC/OAuth flow with external provider.

    Redirects user to provider's authorization page.

    Args:
        provider: OAuth provider (google, github, gitlab)
        request: Starlette request object

    Returns:
        Redirect to provider's authorization URL
    """
    # Validate provider
    if provider not in oidc_service.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}. Supported: {', '.join(oidc_service.SUPPORTED_PROVIDERS)}",
        )

    # Check if provider is configured
    if not oidc_service.is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not configured. Please contact administrator.",
        )

    # Get authorization URL
    try:
        # Callback URL will be /api/auth/callback/{provider}
        redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/auth/callback/{{provider}}"
        # authorize_redirect returns a RedirectResponse directly
        return await oidc_service.get_authorization_url(provider, request, redirect_uri)
    except OIDCServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/callback/{provider}")
async def oidc_callback(
    provider: str, request: Request, code: str, state: Optional[str] = None
):
    """
    Handle OAuth callback from provider.

    Exchanges authorization code for access token, fetches user info,
    creates/updates user, and generates JWT session token.

    Args:
        provider: OAuth provider (google, github, gitlab)
        request: Starlette request object
        code: Authorization code from provider
        state: CSRF protection state (optional)

    Returns:
        Redirect to frontend with token in query parameter
    """
    # Validate provider
    if provider not in oidc_service.SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported provider: {provider}",
        )

    # Check if provider is configured
    if not oidc_service.is_provider_configured(provider):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Provider '{provider}' is not configured",
        )

    try:
        # Exchange code for token
        redirect_uri = f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/auth/callback/{{provider}}"
        token = await oidc_service.exchange_code_for_token(
            provider, request, redirect_uri
        )

        # Get user info from provider
        user_info = await oidc_service.get_user_info(provider, token)

        if not user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get email from provider",
            )

        # Create or update user
        user = user_service.create_or_update_user(
            email=user_info["email"],
            auth_provider=provider,
            name=user_info.get("name"),
        )

        # Generate JWT token
        jwt_token = session_service.create_token(user)

        # Redirect to frontend with token
        from starlette.responses import RedirectResponse

        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:8080")
        redirect_url = f"{frontend_url}/?token={jwt_token}"
        return RedirectResponse(url=redirect_url)

    except OIDCServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OIDC authentication failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}",
        )


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
