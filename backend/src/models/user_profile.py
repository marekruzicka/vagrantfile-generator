"""
User Profile Model.

Represents an authenticated user in public deployment mode.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

from ..utils.validators import validate_email, validate_uuid, normalize_email


class UserProfile(BaseModel):
    """User profile model for authenticated users."""
    
    user_id: str = Field(
        ...,
        description="Unique user identifier (UUID v4)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: str = Field(
        ...,
        description="User's email address (normalized to lowercase)",
        max_length=255,
        examples=["user@example.com"]
    )
    name: str | None = Field(
        None,
        description="Display name from authentication provider",
        max_length=255,
        examples=["John Doe"]
    )
    auth_provider: Literal["email", "google", "github", "gitlab"] = Field(
        ...,
        description="Authentication provider used for this user",
        examples=["email"]
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when user first authenticated (UTC)",
        examples=["2025-11-13T14:30:00Z"]
    )
    last_login: datetime = Field(
        ...,
        description="Most recent login timestamp (UTC)",
        examples=["2025-11-13T15:45:00Z"]
    )
    
    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v: str) -> str:
        """Validate user_id is a valid UUID v4."""
        if not validate_uuid(v):
            raise ValueError(f"Invalid UUID v4 format: {v}")
        return v
    
    @field_validator("email")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        if not validate_email(v):
            raise ValueError(f"Invalid email format: {v}")
        return normalize_email(v)
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe",
                "auth_provider": "email",
                "created_at": "2025-11-13T14:30:00Z",
                "last_login": "2025-11-13T15:45:00Z"
            }
        }
