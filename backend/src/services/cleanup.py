"""
Background cleanup service for expired data.

This service runs periodic tasks to clean up expired OTPs, rate limit entries,
and other temporary data to prevent unbounded growth of the data directory.
"""

import asyncio
import logging
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up expired data."""
    
    def __init__(self):
        """Initialize the cleanup service."""
        self.data_dir = Path(__file__).parent.parent.parent / "data"
        self.auth_dir = self.data_dir / "auth"
        self.users_dir = self.data_dir / "users"
        
    async def cleanup_expired_otps(self) -> int:
        """
        Clean up expired OTP files.
        
        Returns:
            Number of OTP files deleted
        """
        deleted_count = 0
        
        if not self.auth_dir.exists():
            return deleted_count
            
        try:
            current_time = datetime.now()
            
            # Scan all OTP files
            for otp_file in self.auth_dir.glob("otp_*.json"):
                try:
                    with open(otp_file, 'r') as f:
                        otp_data = json.load(f)
                    
                    # Parse expiration time
                    expires_at = datetime.fromisoformat(otp_data.get('expires_at', ''))
                    
                    # Delete if expired
                    if current_time > expires_at:
                        otp_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted expired OTP file: {otp_file.name}")
                        
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Error processing OTP file {otp_file.name}: {e}")
                    # Optionally delete corrupted files
                    otp_file.unlink()
                    deleted_count += 1
                    
        except Exception as e:
            logger.error(f"Error during OTP cleanup: {e}")
            
        return deleted_count
    
    async def cleanup_expired_rate_limits(self) -> int:
        """
        Clean up expired rate limit files.
        
        Returns:
            Number of rate limit files deleted
        """
        deleted_count = 0
        
        if not self.auth_dir.exists():
            return deleted_count
            
        try:
            current_time = datetime.now()
            
            # Scan all rate limit files
            for rate_limit_file in self.auth_dir.glob("ratelimit_*.json"):
                try:
                    with open(rate_limit_file, 'r') as f:
                        rate_limit_data = json.load(f)
                    
                    # Parse reset time
                    reset_at = datetime.fromisoformat(rate_limit_data.get('reset_at', ''))
                    
                    # Delete if expired and no tokens remaining
                    # (Keep active rate limits even if reset_at is old, as they may still have tokens)
                    tokens = rate_limit_data.get('tokens', 0)
                    if current_time > reset_at and tokens >= rate_limit_data.get('max_tokens', 5):
                        # Rate limit has reset and refilled, can be deleted
                        rate_limit_file.unlink()
                        deleted_count += 1
                        logger.info(f"Deleted expired rate limit file: {rate_limit_file.name}")
                        
                except (json.JSONDecodeError, ValueError, KeyError) as e:
                    logger.warning(f"Error processing rate limit file {rate_limit_file.name}: {e}")
                    # Optionally delete corrupted files older than 24 hours
                    if (current_time.timestamp() - rate_limit_file.stat().st_mtime) > 86400:
                        rate_limit_file.unlink()
                        deleted_count += 1
                        
        except Exception as e:
            logger.error(f"Error during rate limit cleanup: {e}")
            
        return deleted_count
    
    async def cleanup_old_sessions(self) -> int:
        """
        Clean up old session files (if we ever store them).
        Currently sessions are JWT-based (stateless), but this is here for future use.
        
        Returns:
            Number of session files deleted
        """
        # Sessions are currently JWT-based (stateless), nothing to clean
        return 0
    
    async def run_cleanup(self):
        """Run all cleanup tasks."""
        logger.info("Starting cleanup tasks...")
        
        otp_deleted = await self.cleanup_expired_otps()
        rate_limit_deleted = await self.cleanup_expired_rate_limits()
        session_deleted = await self.cleanup_old_sessions()
        
        total_deleted = otp_deleted + rate_limit_deleted + session_deleted
        
        if total_deleted > 0:
            logger.info(
                f"Cleanup complete: {otp_deleted} OTPs, "
                f"{rate_limit_deleted} rate limits, "
                f"{session_deleted} sessions deleted"
            )
        else:
            logger.debug("Cleanup complete: no files to delete")


# Singleton instance
_cleanup_service = None


def get_cleanup_service() -> CleanupService:
    """Get or create the cleanup service singleton."""
    global _cleanup_service
    if _cleanup_service is None:
        _cleanup_service = CleanupService()
    return _cleanup_service


async def periodic_cleanup_task(interval_seconds: int = 300):
    """
    Run cleanup tasks periodically.
    
    Args:
        interval_seconds: Interval between cleanup runs in seconds (default: 300 = 5 minutes)
    """
    cleanup_service = get_cleanup_service()
    
    while True:
        try:
            await cleanup_service.run_cleanup()
        except Exception as e:
            logger.error(f"Error in periodic cleanup task: {e}")
        
        await asyncio.sleep(interval_seconds)
