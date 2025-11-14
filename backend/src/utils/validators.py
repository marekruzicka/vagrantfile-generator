"""
Validation utilities.

Provides validation functions for email, UUID, and other common data formats.
"""

import re
import uuid
from typing import Optional


# RFC 5322 simplified email regex
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email or len(email) > 255:
        return False
    
    return bool(EMAIL_REGEX.match(email))


def normalize_email(email: str) -> str:
    """
    Normalize email address to lowercase.
    
    Args:
        email: Email address to normalize
        
    Returns:
        str: Normalized email address
    """
    return email.lower().strip()


def validate_uuid(value: str) -> bool:
    """
    Validate UUID v4 format.
    
    Args:
        value: String to validate as UUID
        
    Returns:
        bool: True if valid UUID v4 format, False otherwise
    """
    try:
        uuid_obj = uuid.UUID(value, version=4)
        return str(uuid_obj) == value
    except (ValueError, AttributeError):
        return False


def generate_uuid() -> str:
    """
    Generate a new UUID v4.
    
    Returns:
        str: UUID v4 as string
    """
    return str(uuid.uuid4())


def validate_otp_code(code: str) -> bool:
    """
    Validate OTP code format (6 digits).
    
    Args:
        code: OTP code to validate
        
    Returns:
        bool: True if valid 6-digit code, False otherwise
    """
    return bool(re.match(r'^\d{6}$', code))
