"""
Rate Limit Record Model.

Represents a rate limit tracking record for OTP requests.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator

from ..utils.validators import validate_email, normalize_email


class RateLimitRecord(BaseModel):
    """Rate limit record for tracking OTP request frequency."""
    
    email: str = Field(
        ...,
        description="Email address being rate limited (normalized to lowercase)",
        max_length=255,
        examples=["user@example.com"]
    )
    timestamps: list[datetime] = Field(
        default_factory=list,
        description="List of request timestamps within the rate limit window",
        examples=[["2025-11-13T14:00:00Z", "2025-11-13T14:15:00Z"]]
    )
    
    @field_validator("email")
    @classmethod
    def validate_and_normalize_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        if not validate_email(v):
            raise ValueError(f"Invalid email format: {v}")
        return normalize_email(v)
    
    def cleanup_old_timestamps(self, window_hours: int = 1) -> None:
        """
        Remove timestamps outside the rate limit window.
        
        Args:
            window_hours: Rate limit window in hours (default: 1)
        """
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=window_hours)
        self.timestamps = [ts for ts in self.timestamps if ts > cutoff]
    
    def add_timestamp(self, timestamp: datetime | None = None) -> None:
        """
        Add a new request timestamp.
        
        Args:
            timestamp: Timestamp to add (defaults to current UTC time)
        """
        if timestamp is None:
            timestamp = datetime.utcnow()
        self.timestamps.append(timestamp)
    
    def is_rate_limited(self, max_requests: int = 5, window_hours: int = 1) -> bool:
        """
        Check if the rate limit has been exceeded.
        
        Args:
            max_requests: Maximum requests allowed in the window (default: 5)
            window_hours: Rate limit window in hours (default: 1)
            
        Returns:
            bool: True if rate limit exceeded, False otherwise
        """
        self.cleanup_old_timestamps(window_hours)
        return len(self.timestamps) >= max_requests
    
    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "timestamps": [
                    "2025-11-13T14:00:00Z",
                    "2025-11-13T14:15:00Z",
                    "2025-11-13T14:30:00Z"
                ]
            }
        }
