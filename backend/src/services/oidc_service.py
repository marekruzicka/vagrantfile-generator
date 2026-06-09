"""
OIDC Service for Vagrantfile Generator.

Handles OAuth/OIDC authentication with external providers (Google, GitHub, GitLab).
"""

import os
import logging
from typing import Dict, Optional, Any
from authlib.integrations.starlette_client import OAuth

logger = logging.getLogger(__name__)


class OIDCServiceError(Exception):
    """Custom exception for OIDC service errors."""

    pass


class OIDCService:
    """Service for handling OIDC/OAuth authentication with external providers."""

    SUPPORTED_PROVIDERS = ["google", "github", "gitlab"]

    def __init__(self):
        """Initialize OIDC service with provider configurations."""
        self.oauth = OAuth()
        self._register_providers()

    def _register_providers(self):
        """
        Register OAuth providers with authlib.

        Reads configuration from environment variables:
        - OIDC_GOOGLE_CLIENT_ID, OIDC_GOOGLE_CLIENT_SECRET
        - OIDC_GITHUB_CLIENT_ID, OIDC_GITHUB_CLIENT_SECRET
        - OIDC_GITLAB_CLIENT_ID, OIDC_GITLAB_CLIENT_SECRET, OIDC_GITLAB_URL
        """
        # Google OAuth configuration
        google_client_id = os.getenv("OIDC_GOOGLE_CLIENT_ID")
        google_client_secret = os.getenv("OIDC_GOOGLE_CLIENT_SECRET")

        if google_client_id and google_client_secret:
            self.oauth.register(
                name="google",
                client_id=google_client_id,
                client_secret=google_client_secret,
                server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
                client_kwargs={"scope": "openid email profile"},
            )
            logger.info("Google OAuth provider registered")
        else:
            logger.warning(
                "Google OAuth not configured - OIDC_GOOGLE_CLIENT_ID/SECRET not set"
            )

        # GitHub OAuth configuration
        github_client_id = os.getenv("OIDC_GITHUB_CLIENT_ID")
        github_client_secret = os.getenv("OIDC_GITHUB_CLIENT_SECRET")

        if github_client_id and github_client_secret:
            self.oauth.register(
                name="github",
                client_id=github_client_id,
                client_secret=github_client_secret,
                authorize_url="https://github.com/login/oauth/authorize",
                authorize_params=None,
                access_token_url="https://github.com/login/oauth/access_token",
                access_token_params=None,
                api_base_url="https://api.github.com/",
                client_kwargs={"scope": "user:email"},
            )
            logger.info("GitHub OAuth provider registered")
        else:
            logger.warning(
                "GitHub OAuth not configured - OIDC_GITHUB_CLIENT_ID/SECRET not set"
            )

        # GitLab OAuth configuration
        gitlab_client_id = os.getenv("OIDC_GITLAB_CLIENT_ID")
        gitlab_client_secret = os.getenv("OIDC_GITLAB_CLIENT_SECRET")
        gitlab_url = os.getenv("OIDC_GITLAB_URL", "https://gitlab.com")

        if gitlab_client_id and gitlab_client_secret:
            self.oauth.register(
                name="gitlab",
                client_id=gitlab_client_id,
                client_secret=gitlab_client_secret,
                authorize_url=f"{gitlab_url}/oauth/authorize",
                authorize_params=None,
                access_token_url=f"{gitlab_url}/oauth/token",
                access_token_params=None,
                api_base_url=f"{gitlab_url}/api/v4/",
                client_kwargs={"scope": "read_user"},
            )
            logger.info(f"GitLab OAuth provider registered ({gitlab_url})")
        else:
            logger.warning(
                "GitLab OAuth not configured - OIDC_GITLAB_CLIENT_ID/SECRET not set"
            )

    def is_provider_configured(self, provider: str) -> bool:
        """
        Check if a provider is configured.

        Args:
            provider: Provider name (google, github, gitlab)

        Returns:
            bool: True if provider is configured, False otherwise
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            return False

        return hasattr(self.oauth, provider)

    async def get_authorization_url(self, provider: str, request, redirect_uri: str):
        """
        Get authorization redirect for OAuth flow.

        Args:
            provider: Provider name (google, github, gitlab)
            request: Starlette request object (needed for session state)
            redirect_uri: Callback URL after authorization

        Returns:
            RedirectResponse to provider's authorization URL

        Raises:
            OIDCServiceError: If provider is not supported or configured
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            logger.warning(f"OIDC login attempt with unsupported provider: {provider}")
            raise OIDCServiceError(f"Unsupported provider: {provider}")

        if not self.is_provider_configured(provider):
            logger.warning(f"OIDC login attempt with unconfigured provider: {provider}")
            raise OIDCServiceError(f"Provider not configured: {provider}")

        try:
            client = getattr(self.oauth, provider)
            redirect_uri_with_provider = redirect_uri.format(provider=provider)

            # Use authorize_redirect which handles session state automatically
            logger.info(f"OIDC: Generating authorization redirect for {provider}")
            return await client.authorize_redirect(request, redirect_uri_with_provider)
        except Exception as e:
            logger.error(f"Failed to get authorization URL for {provider}: {str(e)}")
            raise OIDCServiceError(f"Failed to initiate OAuth flow: {str(e)}")

    async def exchange_code_for_token(
        self, provider: str, request, redirect_uri: str
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.

        Args:
            provider: Provider name (google, github, gitlab)
            request: Starlette request object with authorization code
            redirect_uri: Callback URL (must match the one used in authorization)

        Returns:
            Dict containing access token and metadata

        Raises:
            OIDCServiceError: If exchange fails
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            logger.warning(f"OIDC callback with unsupported provider: {provider}")
            raise OIDCServiceError(f"Unsupported provider: {provider}")

        if not self.is_provider_configured(provider):
            logger.warning(f"OIDC callback with unconfigured provider: {provider}")
            raise OIDCServiceError(f"Provider not configured: {provider}")

        try:
            client = getattr(self.oauth, provider)
            token = await client.authorize_access_token(request)
            logger.info(f"OIDC: Successfully exchanged code for token with {provider}")
            return token
        except Exception as e:
            logger.error(f"Failed to exchange code for token with {provider}: {str(e)}")
            raise OIDCServiceError(f"Token exchange failed: {str(e)}")

    async def get_user_info(
        self, provider: str, token: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fetch user information from provider.

        Args:
            provider: Provider name (google, github, gitlab)
            token: Access token from exchange_code_for_token

        Returns:
            Dict containing user profile (email, name, etc.)

        Raises:
            OIDCServiceError: If user info fetch fails
        """
        if provider not in self.SUPPORTED_PROVIDERS:
            logger.warning(
                f"Attempt to get user info from unsupported provider: {provider}"
            )
            raise OIDCServiceError(f"Unsupported provider: {provider}")

        if not self.is_provider_configured(provider):
            logger.warning(
                f"Attempt to get user info from unconfigured provider: {provider}"
            )
            raise OIDCServiceError(f"Provider not configured: {provider}")

        try:
            client = getattr(self.oauth, provider)

            if provider == "google":
                # Google provides userinfo endpoint
                user_info = await client.userinfo(token=token)
                result = {
                    "email": user_info.get("email"),
                    "name": user_info.get("name"),
                    "provider_user_id": user_info.get("sub"),
                }
                logger.info(
                    f"OIDC: Retrieved user info from Google for {result.get('email')}"
                )
                return result

            elif provider == "github":
                # GitHub requires fetching user endpoint
                resp = await client.get("user", token=token)
                user_data = resp.json()

                # Get primary email
                email_resp = await client.get("user/emails", token=token)
                emails = email_resp.json()
                primary_email = next((e["email"] for e in emails if e["primary"]), None)

                result = {
                    "email": primary_email or user_data.get("email"),
                    "name": user_data.get("name") or user_data.get("login"),
                    "provider_user_id": str(user_data.get("id")),
                }
                logger.info(
                    f"OIDC: Retrieved user info from GitHub for {result.get('email')}"
                )
                return result

            elif provider == "gitlab":
                # GitLab provides user endpoint
                resp = await client.get("user", token=token)
                user_data = resp.json()

                result = {
                    "email": user_data.get("email"),
                    "name": user_data.get("name") or user_data.get("username"),
                    "provider_user_id": str(user_data.get("id")),
                }
                logger.info(
                    f"OIDC: Retrieved user info from GitLab for {result.get('email')}"
                )
                return result

            else:
                raise OIDCServiceError(f"Unknown provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to get user info from {provider}: {str(e)}")
            raise OIDCServiceError(f"Failed to fetch user information: {str(e)}")
