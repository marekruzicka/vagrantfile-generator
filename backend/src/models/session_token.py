"""
Session Token Model.

Represents the JWT token claims structure for authenticated sessions.
"""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator

from ..utils.validators import validate_email, validate_uuid, normalize_email


class SessionToken(BaseModel):
    """JWT session token claims model."""
    
    user_id: str = Field(
        ...,
        description="User identifier (UUID v4)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: str = Field(
        ...,
        description="User's email address (normalized to lowercase)",
        max_length=255,
        examples=["user@example.com"]
    )
    auth_provider: Literal["email", "google", "github", "gitlab"] = Field(
        ...,
        description="Authentication provider used",
        examples=["email"]
    )
    iat: int = Field(
        ...,
        description="Issued at timestamp (Unix epoch)",
        examples=[1699884600]
    )
    exp: int = Field(
        ...,
        description="Expiration timestamp (Unix epoch)",
        examples=[1699971000]
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
    
    @field_validator("exp")
    @classmethod
    def validate_expiration(cls, v: int, info) -> int:
        """Validate expiration is after issued at."""
        if 'iat' in info.data and v <= info.data['iat']:
            raise ValueError("Expiration must be after issued at")
        return v
    
    def is_expired(self) -> bool:
        """Check if this token has expired."""
        return int(datetime.utcnow().timestamp()) >= self.exp
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "auth_provider": "email",
                "iat": 1699884600,
                "exp": 1699971000
            }
        }
