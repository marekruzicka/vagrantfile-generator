"""
User Service.

Handles user profile management and persistence.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from ..models.user_profile import UserProfile
from ..utils.validators import validate_email, validate_uuid, generate_uuid, normalize_email

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing user profiles."""
    
    def __init__(self, base_path: str = "data/users"):
        """Initialize user service with storage configuration."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_or_update_user(
        self,
        email: str,
        name: Optional[str] = None,
        auth_provider: str = "email"
    ) -> UserProfile:
        """
        Create a new user or update existing user's last login.
        
        Args:
            email: User's email address
            name: User's display name (optional)
            auth_provider: Authentication provider used
            
        Returns:
            UserProfile: Created or updated user profile
        """
        email = normalize_email(email)
        
        # Check if user exists
        existing_user = self.get_user_by_email(email)
        
        if existing_user:
            # Update last login
            existing_user.last_login = datetime.utcnow()
            self._save_user(existing_user)
            logger.info(f"Updated last login for user {existing_user.user_id}")
            return existing_user
        else:
            # Create new user
            now = datetime.utcnow()
            user = UserProfile(
                user_id=generate_uuid(),
                email=email,
                name=name or email.split('@')[0],  # Default name from email
                auth_provider=auth_provider,
                created_at=now,
                last_login=now
            )
            
            self._save_user(user)
            logger.info(f"Created new user {user.user_id} for {email}")
            return user
    
    def get_user_by_id(self, user_id: str) -> Optional[UserProfile]:
        """
        Get user profile by ID.
        
        Args:
            user_id: User identifier (UUID)
            
        Returns:
            Optional[UserProfile]: User profile if found, None otherwise
        """
        if not validate_uuid(user_id):
            logger.warning(f"Invalid user ID format: {user_id}")
            return None
        
        profile_path = self.base_path / user_id / "profile.json"
        
        if not profile_path.exists():
            return None
        
        try:
            with open(profile_path, 'r') as f:
                data = json.load(f)
            
            return UserProfile(**data)
        except (json.JSONDecodeError, IOError, ValueError) as e:
            logger.error(f"Failed to load user profile {user_id}: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[UserProfile]:
        """
        Get user profile by email address.
        
        Scans all user directories to find matching email.
        
        Args:
            email: Email address
            
        Returns:
            Optional[UserProfile]: User profile if found, None otherwise
        """
        email = normalize_email(email)
        
        # Scan all user directories
        for user_dir in self.base_path.iterdir():
            if user_dir.is_dir():
                profile_path = user_dir / "profile.json"
                
                if profile_path.exists():
                    try:
                        with open(profile_path, 'r') as f:
                            data = json.load(f)
                        
                        if data.get('email') == email:
                            return UserProfile(**data)
                    except (json.JSONDecodeError, IOError, ValueError) as e:
                        logger.warning(f"Failed to load profile from {profile_path}: {e}")
                        continue
        
        return None
    
    def update_last_login(self, user_id: str) -> Optional[UserProfile]:
        """
        Update user's last login timestamp.
        
        Args:
            user_id: User identifier
            
        Returns:
            Optional[UserProfile]: Updated user profile if found, None otherwise
        """
        user = self.get_user_by_id(user_id)
        
        if user:
            user.last_login = datetime.utcnow()
            self._save_user(user)
            logger.info(f"Updated last login for user {user_id}")
        
        return user
    
    def list_users(self) -> List[UserProfile]:
        """
        List all user profiles.
        
        Returns:
            List[UserProfile]: List of all users
        """
        users = []
        
        for user_dir in self.base_path.iterdir():
            if user_dir.is_dir():
                profile_path = user_dir / "profile.json"
                
                if profile_path.exists():
                    try:
                        with open(profile_path, 'r') as f:
                            data = json.load(f)
                        
                        users.append(UserProfile(**data))
                    except (json.JSONDecodeError, IOError, ValueError) as e:
                        logger.warning(f"Failed to load profile from {profile_path}: {e}")
                        continue
        
        # Sort by last login (most recent first)
        users.sort(key=lambda u: u.last_login, reverse=True)
        
        return users
    
    def _save_user(self, user: UserProfile) -> None:
        """
        Save user profile to file.
        
        Args:
            user: User profile to save
        """
        user_dir = self.base_path / user.user_id
        user_dir.mkdir(parents=True, exist_ok=True)
        
        profile_path = user_dir / "profile.json"
        
        try:
            with open(profile_path, 'w') as f:
                json.dump(user.model_dump(mode='json'), f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save user profile {user.user_id}: {e}")
            raise


# Global user service instance
user_service = UserService()
