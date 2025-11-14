"""
OTP Request Model.

Represents a temporary email OTP verification request.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from ..utils.validators import validate_email, normalize_email


class OTPRequest(BaseModel):
    """OTP request model for email verification."""
    
    email: str = Field(
        ...,
        description="Email address for this OTP request (normalized to lowercase)",
        max_length=255,
        examples=["user@example.com"]
    )
    code: str = Field(
        ...,
        description="6-digit OTP code",
        min_length=6,
        max_length=6,
        examples=["123456"]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when OTP was generated (UTC)",
        examples=["2025-11-13T14:30:00Z"]
    )
    expires_at: datetime = Field(
        ...,
        description="Timestamp when OTP expires (UTC)",
        examples=["2025-11-13T14:45:00Z"]
    )
    attempts: int = Field(
        default=0,
        description="Number of verification attempts made",
        ge=0,
        examples=[0, 1, 2]
    )
    
    @field_validator("email")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        if not validate_email(v):
            raise ValueError(f"Invalid email format: {v}")
        return normalize_email(v)
    
    @field_validator("code")
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate OTP code is 6 digits."""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("OTP code must be 6 digits")
        return v
    
    def is_expired(self) -> bool:
        """Check if this OTP request has expired."""
        return datetime.utcnow() >= self.expires_at
    
    def is_max_attempts_reached(self, max_attempts: int = 3) -> bool:
        """Check if maximum verification attempts have been reached."""
        return self.attempts >= max_attempts
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "code": "123456",
                "created_at": "2025-11-13T14:30:00Z",
                "expires_at": "2025-11-13T14:45:00Z",
                "attempts": 0
            }
        }
