"""
PluginService for Vagrantfile GUI Generator.

This service handles CRUD operations for Vagrant plugin configurations.
"""

import os
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ..models.plugin import Plugin, PluginCreate, PluginUpdate, PluginSummary


class PluginServiceError(Exception):
    """Custom exception for plugin service errors."""
    pass


class PluginService:
    """Service for handling plugin operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the plugin service.
        
        Args:
            base_directory: Base directory for storing plugin files
        """
        self.base_directory = Path(base_directory)
        self.plugins_file = self.base_directory / "plugins.json"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.base_directory.mkdir(parents=True, exist_ok=True)
    
    def _load_plugins_data(self) -> Dict:
        """Load the entire plugins.json file."""
        try:
            if not self.plugins_file.exists():
                return {
                    "plugins": [],
                    "project_plugins": [],
                    "version": "1.0.0",
                    "last_updated": datetime.now().isoformat()
                }
            
            with open(self.plugins_file, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            raise PluginServiceError(f"Failed to load plugins: {str(e)}")
    
    def _save_plugins_data(self, data: Dict):
        """Save the entire plugins.json file."""
        try:
            data["last_updated"] = datetime.now().isoformat()
            
            with open(self.plugins_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise PluginServiceError(f"Failed to save plugins: {str(e)}")
    
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
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            
            # Check if plugin with same name already exists
            if any(p.get("name") == plugin_data.name for p in plugins):
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
                "is_deprecated": plugin_data.is_deprecated,
                "created_at": now,
                "updated_at": now
            }
            
            plugins.append(new_plugin)
            data["plugins"] = plugins
            self._save_plugins_data(data)
            
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
            Plugin if found, None otherwise
        """
        try:
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            
            for plugin in plugins:
                if plugin.get("id") == plugin_id:
                    return Plugin(**plugin)
            
            return None
            
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
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            
            for plugin in plugins:
                if plugin.get("name") == plugin_name:
                    return Plugin(**plugin)
            
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
            PluginServiceError: If plugin name conflicts with another plugin
        """
        try:
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            
            plugin_index = None
            for i, plugin in enumerate(plugins):
                if plugin.get("id") == plugin_id:
                    plugin_index = i
                    break
            
            if plugin_index is None:
                return None
            
            # Check for name conflicts if name is being updated
            if plugin_data.name:
                if any(p.get("name") == plugin_data.name and p.get("id") != plugin_id 
                       for p in plugins):
                    raise PluginServiceError(f"Plugin with name '{plugin_data.name}' already exists")
            
            # Update plugin fields
            existing_plugin = plugins[plugin_index]
            update_dict = plugin_data.model_dump(exclude_unset=True)
            
            for key, value in update_dict.items():
                if value is not None:
                    existing_plugin[key] = value
            
            existing_plugin["updated_at"] = datetime.now().isoformat()
            
            plugins[plugin_index] = existing_plugin
            data["plugins"] = plugins
            self._save_plugins_data(data)
            
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
            True if plugin was deleted, False if not found
        """
        try:
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            project_plugins = data.get("project_plugins", [])
            
            # Find and remove plugin
            initial_length = len(plugins)
            plugins = [p for p in plugins if p.get("id") != plugin_id]
            
            if len(plugins) == initial_length:
                return False
            
            # Also remove any project_plugins associations
            project_plugins = [pp for pp in project_plugins if pp.get("plugin_id") != plugin_id]
            
            data["plugins"] = plugins
            data["project_plugins"] = project_plugins
            self._save_plugins_data(data)
            
            return True
            
        except Exception as e:
            raise PluginServiceError(f"Failed to delete plugin: {str(e)}")
    
    def list_plugins(self) -> List[PluginSummary]:
        """
        List all plugins.
        
        Returns:
            List of plugin summaries
        """
        try:
            data = self._load_plugins_data()
            plugins = data.get("plugins", [])
            
            return [
                PluginSummary(
                    id=plugin.get("id"),
                    name=plugin.get("name"),
                    description=plugin.get("description"),
                    default_version=plugin.get("default_version"),
                    is_deprecated=plugin.get("is_deprecated", False)
                )
                for plugin in plugins
            ]
            
        except Exception as e:
            raise PluginServiceError(f"Failed to list plugins: {str(e)}")
    
    def get_plugins_for_api(self) -> List[Dict]:
        """
        Get plugins formatted for API responses.
        
        Returns:
            List of plugin dictionaries
        """
        try:
            data = self._load_plugins_data()
            return data.get("plugins", [])
            
        except Exception as e:
            raise PluginServiceError(f"Failed to get plugins: {str(e)}")
