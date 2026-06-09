"""
PreferenceService for Vagrantfile Generator.

This service handles user preferences for the application.
Stores preferences in data/users/{user-id}/preferences/settings.json
"""

import json
from typing import Optional, List
from pathlib import Path
from pydantic import BaseModel, Field

from .file_service import FileService


class UserPreferences(BaseModel):
    """User preferences model."""
    show_shared_resources: bool = True
    favorite_plugins: List[str] = Field(default_factory=list)
    favorite_provisioners: List[str] = Field(default_factory=list)
    favorite_triggers: List[str] = Field(default_factory=list)
    favorite_boxes: List[str] = Field(default_factory=list)


class PreferenceServiceError(Exception):
    """Custom exception for preference service errors."""
    pass


class PreferenceService:
    """Service for handling user preferences."""
    
    def __init__(self, user_id: Optional[str] = None):
        """
        Initialize the preference service.
        
        Args:
            user_id: User ID for user-specific preferences. If None, returns defaults.
        """
        self.user_id = user_id
        self.file_service = FileService()
        
        if user_id:
            self.preferences_dir = self.file_service.get_user_data_path(user_id, "preferences")
            self.preferences_dir.mkdir(parents=True, exist_ok=True)
            self.settings_file = self.preferences_dir / "settings.json"
        else:
            self.preferences_dir = None
            self.settings_file = None
    
    def get_preferences(self) -> UserPreferences:
        """
        Get user preferences.
        
        Returns:
            UserPreferences object with user's settings
        """
        # If no user_id, return defaults
        if not self.user_id or not self.settings_file:
            return UserPreferences()
        
        # If settings file doesn't exist, return defaults
        if not self.settings_file.exists():
            return UserPreferences()
        
        # Load settings from file
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return UserPreferences(**data)
        except Exception as e:
            raise PreferenceServiceError(f"Failed to load preferences: {e}")
    
    def update_preferences(self, preferences: UserPreferences) -> UserPreferences:
        """
        Update user preferences.
        
        Args:
            preferences: New preferences to save
            
        Returns:
            Updated preferences
            
        Raises:
            PreferenceServiceError: If user_id is not set or save fails
        """
        if not self.user_id or not self.settings_file:
            raise PreferenceServiceError("Cannot update preferences without user_id")
        
        try:
            # Save to file
            self.file_service.atomic_write_json(self.settings_file, preferences.dict())
            
            return preferences
        except Exception as e:
            raise PreferenceServiceError(f"Failed to save preferences: {e}")
    
    def get_show_shared_resources(self) -> bool:
        """
        Get the show_shared_resources preference.
        
        Returns:
            True if shared resources should be shown, False otherwise
        """
        preferences = self.get_preferences()
        return preferences.show_shared_resources
    
    def set_show_shared_resources(self, show: bool) -> bool:
        """
        Set the show_shared_resources preference.
        
        Args:
            show: Whether to show shared resources
            
        Returns:
            The updated preference value
        """
        preferences = self.get_preferences()
        preferences.show_shared_resources = show
        self.update_preferences(preferences)
        return show
    
    # Favorites management methods
    
    def get_favorites(self, resource_type: str) -> List[str]:
        """
        Get favorite resource IDs for a specific resource type.
        
        Args:
            resource_type: Type of resource ('plugins', 'provisioners', 'triggers', 'boxes')
            
        Returns:
            List of favorite resource IDs
        """
        preferences = self.get_preferences()
        field_name = f"favorite_{resource_type}"
        return getattr(preferences, field_name, [])
    
    def add_favorite(self, resource_type: str, resource_id: str) -> bool:
        """
        Add a resource to favorites.
        
        Args:
            resource_type: Type of resource ('plugins', 'provisioners', 'triggers', 'boxes')
            resource_id: ID of the resource to favorite
            
        Returns:
            True if added, False if already favorited
        """
        if not self.user_id:
            raise PreferenceServiceError("Cannot manage favorites without user_id")
        
        preferences = self.get_preferences()
        field_name = f"favorite_{resource_type}"
        favorites = getattr(preferences, field_name, [])
        
        if resource_id in favorites:
            return False
        
        favorites.append(resource_id)
        setattr(preferences, field_name, favorites)
        self.update_preferences(preferences)
        return True
    
    def remove_favorite(self, resource_type: str, resource_id: str) -> bool:
        """
        Remove a resource from favorites.
        
        Args:
            resource_type: Type of resource ('plugins', 'provisioners', 'triggers', 'boxes')
            resource_id: ID of the resource to unfavorite
            
        Returns:
            True if removed, False if not in favorites
        """
        if not self.user_id:
            raise PreferenceServiceError("Cannot manage favorites without user_id")
        
        preferences = self.get_preferences()
        field_name = f"favorite_{resource_type}"
        favorites = getattr(preferences, field_name, [])
        
        if resource_id not in favorites:
            return False
        
        favorites.remove(resource_id)
        setattr(preferences, field_name, favorites)
        self.update_preferences(preferences)
        return True
    
    def is_favorite(self, resource_type: str, resource_id: str) -> bool:
        """
        Check if a resource is favorited.
        
        Args:
            resource_type: Type of resource ('plugins', 'provisioners', 'triggers', 'boxes')
            resource_id: ID of the resource to check
            
        Returns:
            True if favorited, False otherwise
        """
        preferences = self.get_preferences()
        field_name = f"favorite_{resource_type}"
        favorites = getattr(preferences, field_name, [])
        return resource_id in favorites
