"""
OTP Service.

Handles OTP generation, storage, verification, and cleanup.
"""

import os
import re
import json
import secrets
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..models.otp_request import OTPRequest
from ..utils.validators import validate_email, normalize_email
from .file_service import FileService

logger = logging.getLogger(__name__)

# Built-in test user configuration
# Backward-compatible single-user variables:
#   TEST_USER_EMAIL=test@example.com
#   TEST_USER_OTP=123456
# Multi-user variables:
#   TEST_USER_EMAIL_1=test@example.com
#   TEST_USER_OTP_1=123456
#   TEST_USER_EMAIL_2=test2@example.com
#   TEST_USER_OTP_2=123456
# TEST_USER_ENABLED gates all static test users.
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "test@example.com")
TEST_USER_OTP = os.getenv("TEST_USER_OTP", "123456")
TEST_USER_ENABLED = os.getenv("TEST_USER_ENABLED", "false").lower() == "true"


def load_test_users() -> dict[str, str]:
    """Load static test users from environment variables.

    Supports the legacy TEST_USER_EMAIL/TEST_USER_OTP pair and any indexed
    TEST_USER_EMAIL_<number>/TEST_USER_OTP_<number> pairs. The global
    TEST_USER_ENABLED flag enables or disables all static test users.
    """
    if not TEST_USER_ENABLED:
        return {}

    users: dict[str, str] = {}

    indexed_pattern = re.compile(r"^TEST_USER_EMAIL_(\d+)$")
    indexes = sorted(
        int(match.group(1))
        for key in os.environ
        if (match := indexed_pattern.match(key))
    )

    # Preserve backward compatibility with existing single test user settings.
    # If indexed users are configured, do not implicitly add the default
    # test@example.com user unless legacy variables were explicitly set.
    legacy_configured = "TEST_USER_EMAIL" in os.environ or "TEST_USER_OTP" in os.environ
    if TEST_USER_EMAIL and TEST_USER_OTP and (legacy_configured or not indexes):
        users[normalize_email(TEST_USER_EMAIL)] = TEST_USER_OTP

    for index in indexes:
        email = os.getenv(f"TEST_USER_EMAIL_{index}")
        otp = os.getenv(f"TEST_USER_OTP_{index}")

        if not email:
            continue
        if not otp:
            logger.warning(
                "Ignoring TEST_USER_EMAIL_%s because TEST_USER_OTP_%s is not set",
                index,
                index,
            )
            continue

        users[normalize_email(email)] = otp

    return users


class OTPService:
    """Service for managing email OTP authentication."""

    def __init__(self, storage_path: str = "data/auth/otp-requests.json"):
        """Initialize OTP service with storage configuration."""
        self.storage_path = Path(storage_path)
        self.otp_length = int(os.getenv("OTP_LENGTH", "6"))
        self.expiration_minutes = int(os.getenv("OTP_EXPIRATION_MINUTES", "15"))
        self.max_attempts = int(os.getenv("OTP_MAX_ATTEMPTS", "3"))
        self.file_service = FileService()

        # Test user configuration
        self.test_users = load_test_users()

        if self.test_users:
            logger.warning(
                "Static OTP test users enabled: %s",
                ", ".join(sorted(self.test_users.keys())),
            )

        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def is_test_user(self, email: str) -> bool:
        """Check if email is a configured static OTP test user."""
        return normalize_email(email) in self.test_users

    def get_test_user_otp(self, email: str) -> Optional[str]:
        """Get static OTP for a configured test user, if any."""
        return self.test_users.get(normalize_email(email))

    def generate_otp(self, email: str) -> OTPRequest:
        """
        Generate a new OTP code for an email address.

        Args:
            email: Email address to generate OTP for

        Returns:
            OTPRequest: Generated OTP request

        Raises:
            ValueError: If email is invalid
        """
        if not validate_email(email):
            raise ValueError(f"Invalid email address: {email}")

        email = normalize_email(email)

        # Use static OTP for configured test users
        test_user_otp = self.get_test_user_otp(email)
        if test_user_otp:
            code = test_user_otp
            logger.info(f"Using static OTP for test user {email}")
        else:
            # Generate random OTP code
            code = "".join(secrets.choice("0123456789") for _ in range(self.otp_length))

        # Calculate expiration
        now = datetime.utcnow()
        expires_at = now + timedelta(minutes=self.expiration_minutes)

        otp_request = OTPRequest(
            email=email, code=code, created_at=now, expires_at=expires_at, attempts=0
        )

        logger.info(f"Generated OTP for {email}, expires at {expires_at}")
        return otp_request

    def store_otp(self, otp_request: OTPRequest) -> None:
        """
        Store OTP request to file.

        Args:
            otp_request: OTP request to store
        """
        # Load existing requests
        requests = self._load_requests()

        # Store by email (replaces any existing OTP for this email)
        requests[otp_request.email] = otp_request.model_dump(mode="json")

        # Save to file
        self._save_requests(requests)

        logger.info(f"Stored OTP for {otp_request.email}")

    def verify_otp(self, email: str, code: str) -> bool:
        """
        Verify an OTP code.

        Args:
            email: Email address
            code: OTP code to verify

        Returns:
            bool: True if code is valid, False otherwise
        """
        email = normalize_email(email)

        # Load requests
        requests = self._load_requests()

        # Check if OTP exists for this email
        if email not in requests:
            logger.warning(f"OTP verification failed: No OTP found for {email}")
            return False

        # Parse OTP request
        otp_data = requests[email]
        otp_request = OTPRequest(**otp_data)

        # Check expiration
        if otp_request.is_expired():
            logger.warning(f"OTP verification failed: OTP expired for {email}")
            # Clean up expired OTP
            del requests[email]
            self._save_requests(requests)
            return False

        # Check max attempts
        if otp_request.is_max_attempts_reached(self.max_attempts):
            logger.warning(f"OTP verification failed: Max attempts reached for {email}")
            # Clean up after max attempts
            del requests[email]
            self._save_requests(requests)
            return False

        # Increment attempts
        otp_request.attempts += 1
        requests[email] = otp_request.model_dump(mode="json")
        self._save_requests(requests)

        # Verify code
        if otp_request.code == code:
            logger.info(f"OTP verification successful for {email}")
            # Remove OTP after successful verification
            del requests[email]
            self._save_requests(requests)
            return True
        else:
            logger.warning(
                f"OTP verification failed: Invalid code for {email} (attempt {otp_request.attempts}/{self.max_attempts})"
            )
            return False

    def get_otp(self, email: str) -> Optional[OTPRequest]:
        """
        Get OTP request for an email (for testing/debugging).

        Args:
            email: Email address

        Returns:
            Optional[OTPRequest]: OTP request if exists, None otherwise
        """
        email = normalize_email(email)
        requests = self._load_requests()

        if email not in requests:
            return None

        return OTPRequest(**requests[email])

    def cleanup_expired_otps(self) -> int:
        """
        Remove expired OTP requests.

        Returns:
            int: Number of expired OTPs removed
        """
        requests = self._load_requests()
        initial_count = len(requests)

        # Filter out expired OTPs
        now = datetime.utcnow()
        active_requests = {
            email: data
            for email, data in requests.items()
            if datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00")) > now
        }

        removed_count = initial_count - len(active_requests)

        if removed_count > 0:
            self._save_requests(active_requests)
            logger.info(f"Cleaned up {removed_count} expired OTP requests")

        return removed_count

    def _load_requests(self) -> dict:
        """Load OTP requests from file."""
        if not self.storage_path.exists():
            return {}

        try:
            with open(self.storage_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load OTP requests: {e}")
            return {}

    def _save_requests(self, requests: dict) -> None:
        """Save OTP requests to file."""
        try:
            self.file_service.atomic_write_json(self.storage_path, requests)
        except IOError as e:
            logger.error(f"Failed to save OTP requests: {e}")
            raise


# Global OTP service instance
otp_service = OTPService()
