"""
Rate Limit Service.

Handles rate limiting for OTP requests using token bucket algorithm.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from ..models.rate_limit import RateLimitRecord
from ..utils.validators import validate_email, normalize_email

logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for rate limiting OTP requests."""
    
    def __init__(self, storage_path: str = "data/auth/rate-limits.json"):
        """Initialize rate limit service with storage configuration."""
        self.storage_path = Path(storage_path)
        self.max_requests = int(os.getenv("OTP_RATE_LIMIT_MAX_REQUESTS", "5"))
        self.window_hours = int(os.getenv("OTP_RATE_LIMIT_WINDOW_HOURS", "1"))
        
        # Ensure storage directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    def check_rate_limit(self, email: str) -> bool:
        """
        Check if an email has exceeded the rate limit.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if rate limited (exceeded limit), False if allowed
        """
        if not validate_email(email):
            raise ValueError(f"Invalid email address: {email}")
        
        email = normalize_email(email)
        
        # Load records
        records = self._load_records()
        
        # Get or create record for this email
        if email in records:
            record_data = records[email]
            record = RateLimitRecord(**record_data)
        else:
            record = RateLimitRecord(email=email, timestamps=[])
        
        # Check if rate limited
        is_limited = record.is_rate_limited(self.max_requests, self.window_hours)
        
        if is_limited:
            logger.warning(
                f"Rate limit exceeded for {email}: "
                f"{len(record.timestamps)} requests in last {self.window_hours} hour(s)"
            )
        
        return is_limited
    
    def record_request(self, email: str, timestamp: Optional[datetime] = None) -> None:
        """
        Record a request for rate limiting.
        
        Args:
            email: Email address
            timestamp: Request timestamp (defaults to current UTC time)
        """
        email = normalize_email(email)
        
        # Load records
        records = self._load_records()
        
        # Get or create record for this email
        if email in records:
            record_data = records[email]
            record = RateLimitRecord(**record_data)
        else:
            record = RateLimitRecord(email=email, timestamps=[])
        
        # Add timestamp
        record.add_timestamp(timestamp)
        
        # Clean up old timestamps
        record.cleanup_old_timestamps(self.window_hours)
        
        # Save updated record
        records[email] = record.model_dump(mode='json')
        self._save_records(records)
        
        logger.debug(f"Recorded request for {email} ({len(record.timestamps)} in window)")
    
    def get_remaining_requests(self, email: str) -> int:
        """
        Get the number of remaining requests allowed for an email.
        
        Args:
            email: Email address
            
        Returns:
            int: Number of requests remaining (0 if rate limited)
        """
        email = normalize_email(email)
        
        # Load records
        records = self._load_records()
        
        if email not in records:
            return self.max_requests
        
        record_data = records[email]
        record = RateLimitRecord(**record_data)
        record.cleanup_old_timestamps(self.window_hours)
        
        remaining = max(0, self.max_requests - len(record.timestamps))
        return remaining
    
    def cleanup_old_records(self) -> int:
        """
        Remove rate limit records older than the window.
        
        Returns:
            int: Number of records removed
        """
        records = self._load_records()
        initial_count = len(records)
        
        # Filter out old records
        cutoff = datetime.utcnow() - timedelta(hours=self.window_hours)
        active_records = {}
        
        for email, data in records.items():
            record = RateLimitRecord(**data)
            record.cleanup_old_timestamps(self.window_hours)
            
            # Keep record if it still has timestamps
            if record.timestamps:
                active_records[email] = record.model_dump(mode='json')
        
        removed_count = initial_count - len(active_records)
        
        if removed_count > 0:
            self._save_records(active_records)
            logger.info(f"Cleaned up {removed_count} old rate limit records")
        
        return removed_count
    
    def _load_records(self) -> dict:
        """Load rate limit records from file."""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Failed to load rate limit records: {e}")
            return {}
    
    def _save_records(self, records: dict) -> None:
        """Save rate limit records to file."""
        try:
            self.file_service.atomic_write_json(self.storage_path, records)
        except IOError as e:
            logger.error(f"Failed to save rate limit records: {e}")
            raise


# Global rate limit service instance
rate_limit_service = RateLimitService()
