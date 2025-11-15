"""
PluginService for Vagrantfile Generator.

This service handles CRUD operations for Vagrant plugin configurations.
Uses individual JSON files for each plugin stored in data/plugins/ directory.
"""

import os
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ..models.plugin import Plugin, PluginCreate, PluginUpdate, PluginSummary
from .file_service import FileService


class PluginServiceError(Exception):
    """Custom exception for plugin service errors."""
    pass


class PluginService:
    """Service for handling plugin operations using file-based storage."""
    
    def __init__(self, base_directory: str = "data", user_id: Optional[str] = None, show_shared: Optional[bool] = None):
        """
        Initialize the plugin service.
        
        Args:
            base_directory: Base directory for storing plugin files (deprecated, use user_id)
            user_id: User ID for user-specific storage. If None, uses shared directory.
            show_shared: Override for show_shared_resources preference (for testing)
        """
        # Support user-specific directories
        if user_id:
            file_service = FileService()
            self.plugins_directory = file_service.get_user_data_path(user_id, "plugins")
        else:
            # For backward compatibility and self-hosted mode
            if base_directory == "data":
                # Use shared directory in new multi-user setup
                file_service = FileService()
                self.plugins_directory = file_service.get_shared_data_path("plugins")
            else:
                # Legacy direct path specification
                self.base_directory = Path(base_directory)
                self.plugins_directory = self.base_directory / "plugins"
        
        self.user_id = user_id
        self.file_service = FileService()
        self.data_dir = self.plugins_directory  # Alias for backwards compatibility
        
        # Load show_shared preference
        if show_shared is not None:
            self.show_shared = show_shared
        else:
            self.show_shared = self._load_show_shared_preference()
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _load_show_shared_preference(self) -> bool:
        """Load user's preference for showing shared resources."""
        if not self.user_id:
            return True  # Self-hosted mode: always show shared
        
        from .preference_service import PreferenceService
        pref_service = PreferenceService(self.user_id)
        return pref_service.get_show_shared_resources()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.plugins_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_plugin_file_path(self, plugin_id: str) -> Path:
        """Get the file path for a specific plugin."""
        return self.plugins_directory / f"{plugin_id}.json"
    
    def _load_plugin_from_file(self, plugin_id: str) -> Optional[Dict]:
        """Load a plugin from its JSON file."""
        try:
            plugin_file = self._get_plugin_file_path(plugin_id)
            
            # Try user directory first, then shared directory
            if not plugin_file.exists() and self.user_id:
                file_service = FileService()
                shared_path = file_service.get_shared_data_path("plugins") / f"{plugin_id}.json"
                if shared_path.exists():
                    plugin_file = shared_path
            
            if not plugin_file.exists():
                return None
            
            with open(plugin_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            raise PluginServiceError(f"Failed to load plugin {plugin_id}: {str(e)}")
    
    def _save_plugin_to_file(self, plugin_data: Dict):
        """Save a plugin to its JSON file."""
        try:
            plugin_id = plugin_data.get("id")
            if not plugin_id:
                raise PluginServiceError("Plugin ID is required for saving")
            
            plugin_file = self._get_plugin_file_path(plugin_id)
            plugin_data["updated_at"] = datetime.now().isoformat()
            
            with open(plugin_file, 'w', encoding='utf-8') as f:
                json.dump(plugin_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise PluginServiceError(f"Failed to save plugin: {str(e)}")
    
    def _delete_plugin_file(self, plugin_id: str) -> bool:
        """Delete a plugin's JSON file."""
        try:
            plugin_file = self._get_plugin_file_path(plugin_id)
            
            if plugin_file.exists():
                plugin_file.unlink()
                return True
            
            return False
                
        except Exception as e:
            raise PluginServiceError(f"Failed to delete plugin file: {str(e)}")
    
    def _list_all_plugin_ids(self) -> List[str]:
        """List all plugin IDs from the plugins directory."""
        try:
            plugin_ids = []
            
            for file_path in self.plugins_directory.glob("*.json"):
                plugin_id = file_path.stem  # Get filename without .json extension
                plugin_ids.append(plugin_id)
            
            return plugin_ids
                
        except Exception as e:
            raise PluginServiceError(f"Failed to list plugin IDs: {str(e)}")
    
    def _check_name_conflict(self, plugin_name: str, exclude_id: Optional[str] = None) -> bool:
        """Check if a plugin name already exists (excluding a specific ID)."""
        try:
            plugin_ids = self._list_all_plugin_ids()
            
            for plugin_id in plugin_ids:
                if exclude_id and plugin_id == exclude_id:
                    continue
                
                plugin_data = self._load_plugin_from_file(plugin_id)
                if plugin_data and plugin_data.get("name") == plugin_name:
                    return True
            
            return False
                
        except Exception as e:
            raise PluginServiceError(f"Failed to check name conflict: {str(e)}")
    
    def create_plugin(self, plugin_data: PluginCreate) -> Plugin:
        """
        Create a new plugin.
        
        Args:
            plugin_data: Plugin creation data
            
        Returns:
            Created plugin
            
        Raises:
            PluginServiceError: If plugin with same name already exists
        """
        try:
            # Check if plugin with same name already exists
            if self._check_name_conflict(plugin_data.name):
                raise PluginServiceError(f"Plugin with name '{plugin_data.name}' already exists")
            
            # Create new plugin
            now = datetime.now().isoformat()
            new_plugin = {
                "id": str(uuid.uuid4()),
                "name": plugin_data.name,
                "description": plugin_data.description,
                "source_url": plugin_data.source_url,
                "documentation_url": plugin_data.documentation_url,
                "default_version": plugin_data.default_version,
                "configuration": plugin_data.configuration,
                "is_deprecated": plugin_data.is_deprecated,
                "created_at": now,
                "updated_at": now
            }
            
            self._save_plugin_to_file(new_plugin)
            
            return Plugin(**new_plugin)
            
        except PluginServiceError:
            raise
        except Exception as e:
            raise PluginServiceError(f"Failed to create plugin: {str(e)}")
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """
        Get a specific plugin by ID.
        
        Args:
            plugin_id: Plugin ID to retrieve
            
        Returns:
            Plugin if found and user has access, None otherwise
        """
        try:
            plugin_data = self._load_plugin_from_file(plugin_id)
            
            if not plugin_data:
                return None
            
            # Apply is_shared and owner_id metadata based on deployment mode
            plugin_data = self.file_service.apply_shared_metadata(
                plugin_data, plugin_id, "plugins", self.user_id
            )
            
            return Plugin(**plugin_data)
            
        except Exception as e:
            raise PluginServiceError(f"Failed to get plugin: {str(e)}")
    
    def get_plugin_by_name(self, plugin_name: str) -> Optional[Plugin]:
        """
        Get a specific plugin by name.
        
        Args:
            plugin_name: Plugin name to retrieve
            
        Returns:
            Plugin if found, None otherwise
        """
        try:
            # Use list_plugins which already merges shared and user resources
            plugins = self.list_plugins(include_deprecated=True)
            
            for plugin in plugins:
                if plugin.name == plugin_name:
                    return plugin
            
            return None
            
        except Exception as e:
            raise PluginServiceError(f"Failed to get plugin by name: {str(e)}")
    
    def update_plugin(self, plugin_id: str, plugin_data: PluginUpdate) -> Optional[Plugin]:
        """
        Update an existing plugin.
        
        Args:
            plugin_id: Plugin ID to update
            plugin_data: Plugin update data
            
        Returns:
            Updated plugin if found, None otherwise
            
        Raises:
            PluginServiceError: If plugin name conflicts with another plugin or if trying to edit shared resource
        """
        try:
            existing_plugin = self._load_plugin_from_file(plugin_id)
            
            if not existing_plugin:
                return None
            
            # Check if trying to edit a shared resource in public mode
            if self.user_id:
                # In public mode, check if this plugin is in shared directory
                user_file = self.data_dir / f"{plugin_id}.json"
                if not user_file.exists():
                    raise PluginServiceError("Cannot edit shared resources")
            
            # Check for name conflicts if name is being updated
            if plugin_data.name and plugin_data.name != existing_plugin.get("name"):
                if self._check_name_conflict(plugin_data.name, exclude_id=plugin_id):
                    raise PluginServiceError(f"Plugin with name '{plugin_data.name}' already exists")
            
            # Update plugin fields
            update_dict = plugin_data.model_dump(exclude_unset=True)
            
            for key, value in update_dict.items():
                if value is not None:
                    existing_plugin[key] = value
            
            self._save_plugin_to_file(existing_plugin)
            
            return Plugin(**existing_plugin)
            
        except PluginServiceError:
            raise
        except Exception as e:
            raise PluginServiceError(f"Failed to update plugin: {str(e)}")
    
    def delete_plugin(self, plugin_id: str) -> bool:
        """
        Delete a plugin.
        
        Args:
            plugin_id: Plugin ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            PluginServiceError: If trying to delete shared resource
        """
        try:
            # Check if trying to delete a shared resource in public mode
            if self.user_id:
                user_file = self.data_dir / f"{plugin_id}.json"
                if not user_file.exists():
                    raise PluginServiceError("Cannot delete shared resources")
            
            return self._delete_plugin_file(plugin_id)
            
        except Exception as e:
            raise PluginServiceError(f"Failed to delete plugin: {str(e)}")
    
    def list_plugins(self, include_deprecated: bool = True) -> List[Plugin]:
        """
        List all plugins (merged shared + user-specific).
        Filters based on show_shared_resources preference.
        
        Args:
            include_deprecated: Whether to include deprecated plugins
            
        Returns:
            List of plugins with is_shared and owner_id fields
        """
        try:
            file_service = FileService()
            
            # Loader function for merge_resources
            def load_plugin_data(file_path: Path) -> dict:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Merge shared and user resources
            merged_data = file_service.merge_resources(
                user_id=self.user_id,
                resource_type="plugins",
                loader_func=load_plugin_data
            )
            
            plugins = []
            
            # Load favorites if user is authenticated
            favorite_ids = []
            if self.user_id:
                from .preference_service import PreferenceService
                pref_service = PreferenceService(self.user_id)
                favorite_ids = pref_service.get_favorites('plugins')
            
            for plugin_data in merged_data:
                plugin = Plugin(**plugin_data)
                
                # Filter based on preferences
                # Show resource if: not shared, OR show_shared=True, OR is a favorite
                if plugin.is_shared and not self.show_shared and plugin.id not in favorite_ids:
                    continue
                
                if include_deprecated or not plugin.is_deprecated:
                    plugins.append(plugin)
            
            # Sort by name
            plugins.sort(key=lambda p: p.name.lower())
            
            return plugins
            
        except Exception as e:
            raise PluginServiceError(f"Failed to list plugins: {str(e)}")
    
    def list_plugins_summary(self, include_deprecated: bool = True) -> List[PluginSummary]:
        """
        List all plugins as summaries (lightweight version).
        
        Args:
            include_deprecated: Whether to include deprecated plugins
            
        Returns:
            List of plugin summaries
        """
        try:
            plugins = self.list_plugins(include_deprecated=include_deprecated)
            
            return [
                PluginSummary(
                    id=plugin.id,
                    name=plugin.name,
                    description=plugin.description,
                    default_version=plugin.default_version,
                    is_deprecated=plugin.is_deprecated
                )
                for plugin in plugins
            ]
            
        except Exception as e:
            raise PluginServiceError(f"Failed to list plugin summaries: {str(e)}")
    
    def copy_shared_plugin(self, plugin_id: str) -> Plugin:
        """
        Create a copy of a shared plugin in user's directory.
        User can then edit/customize their copy.
        
        Args:
            plugin_id: ID of the shared plugin to copy
            
        Returns:
            Copied plugin with new ID
            
        Raises:
            PluginServiceError: If plugin not found, not shared, or user_id not set
        """
        if not self.user_id:
            raise PluginServiceError("Cannot copy plugins in self-hosted mode")
        
        try:
            # Load shared plugin
            shared_file = self.file_service.get_shared_data_path("plugins") / f"{plugin_id}.json"
            
            if not shared_file.exists():
                raise PluginServiceError(f"Shared plugin {plugin_id} not found")
            
            with open(shared_file, 'r', encoding='utf-8') as f:
                plugin_data = json.load(f)
            
            # Verify it's a shared resource
            if not plugin_data.get("is_shared", False):
                raise PluginServiceError("Can only copy shared resources")
            
            # Generate new ID for the copy
            new_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create copy with new metadata
            plugin_copy = {
                **plugin_data,
                "id": new_id,
                "name": f"{plugin_data['name']} (Copy)",
                "is_shared": False,
                "owner_id": self.user_id,
                "source_id": plugin_id,  # Track original shared resource
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory
            user_file = self.file_service.get_user_data_path(self.user_id, "plugins") / f"{new_id}.json"
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(plugin_copy, f, indent=2, ensure_ascii=False)
            
            return Plugin(**plugin_copy)
            
        except Exception as e:
            raise PluginServiceError(f"Failed to copy plugin: {str(e)}")
    
    def get_copies_of_shared_resource(self, source_id: str) -> List[Plugin]:
        """
        Get all user's copies of a specific shared resource.
        
        Args:
            source_id: ID of the original shared resource
            
        Returns:
            List of plugins that were copied from the specified shared resource
            
        Raises:
            PluginServiceError: If user_id not set
        """
        if not self.user_id:
            return []  # Self-hosted mode has no copies
        
        try:
            # List all user plugins and filter by source_id
            all_plugins = self.list_plugins()
            copies = [p for p in all_plugins if p.source_id == source_id]
            return copies
            
        except Exception as e:
            raise PluginServiceError(f"Failed to get copies: {str(e)}")
