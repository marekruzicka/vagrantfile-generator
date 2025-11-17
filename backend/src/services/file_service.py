"""
FileService for Vagrantfile Generator.

This service handles file I/O operations for multi-user data storage.
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path


class FileServiceError(Exception):
    """Custom exception for file service errors."""
    pass


class FileService:
    """Service for handling project file operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the file service.
        
        Args:
            base_directory: Base directory for storing project files
        """
        self.base_directory = Path(base_directory)
        self.shared_directory = self.base_directory / "shared"
        self.users_directory = self.base_directory / "users"
        self.auth_directory = self.base_directory / "auth"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        directories = [
            self.base_directory,
            self.shared_directory,
            self.users_directory,
            self.auth_directory
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def get_user_data_path(self, user_id: str, resource_type: str = "") -> Path:
        """
        Get the data directory path for a specific user.
        
        Args:
            user_id: User identifier (UUID)
            resource_type: Optional resource type subdirectory (e.g., "projects", "boxes")
            
        Returns:
            Path: Path to user's data directory
        """
        user_path = self.users_directory / user_id
        
        if resource_type:
            user_path = user_path / resource_type
        
        # Ensure directory exists
        user_path.mkdir(parents=True, exist_ok=True)
        
        return user_path
    
    def get_shared_data_path(self, resource_type: str = "") -> Path:
        """
        Get the shared data directory path.
        
        Args:
            resource_type: Optional resource type subdirectory (e.g., "projects", "boxes")
            
        Returns:
            Path: Path to shared data directory
        """
        shared_path = self.shared_directory
        
        if resource_type:
            shared_path = shared_path / resource_type
        
        # Ensure directory exists
        shared_path.mkdir(parents=True, exist_ok=True)
        
        return shared_path
    
    def merge_resources(
        self,
        user_id: Optional[str],
        resource_type: str,
        loader_func
    ) -> List[Dict[str, Any]]:
        """
        Merge shared and user-specific resources.
        
        Loads resources from shared directory and user directory (if user_id provided),
        adding an is_shared flag to each resource.
        
        Args:
            user_id: User identifier (None for self-hosted mode)
            resource_type: Resource type subdirectory (e.g., "projects", "boxes")
            loader_func: Function to load individual resource files (takes Path, returns dict)
            
        Returns:
            List of resources with is_shared and owner_id fields added
        """
        resources = []
        
        # Load shared resources
        shared_path = self.get_shared_data_path(resource_type)
        if shared_path.exists():
            for file_path in shared_path.glob("*.json"):
                try:
                    resource = loader_func(file_path)
                    # In self-hosted mode (user_id=None): is_shared=False (everything is editable)
                    # In public mode (user_id set): is_shared=True (shared resources are read-only)
                    resource["is_shared"] = user_id is not None
                    # Set owner_id to None for shared resources
                    resource["owner_id"] = None
                    resources.append(resource)
                except Exception as e:
                    # Log error but continue with other resources
                    import logging
                    logging.warning(f"Failed to load shared resource {file_path}: {str(e)}")
        
        # Load user-specific resources (if in public mode)
        if user_id:
            user_path = self.get_user_data_path(user_id, resource_type)
            if user_path.exists():
                for file_path in user_path.glob("*.json"):
                    try:
                        resource = loader_func(file_path)
                        resource["is_shared"] = False
                        resource["owner_id"] = user_id
                        resources.append(resource)
                    except Exception as e:
                        import logging
                        logging.warning(f"Failed to load user resource {file_path}: {str(e)}")
        
        return resources
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the file service.
        
        Returns:
            Dictionary with health status
        """
        health = {
            "status": "healthy",
            "issues": [],
            "directories_exist": True,
            "writable": True
        }
        
        try:
            # Check directories exist
            for directory in [self.base_directory, self.shared_directory, self.users_directory, self.auth_directory]:
                if not directory.exists():
                    health["issues"].append(f"Directory missing: {directory}")
                    health["directories_exist"] = False
            
            # Check write permissions
            test_file = self.base_directory / "health_check_test.tmp"
            try:
                test_file.write_text("test")
                test_file.unlink()
            except Exception:
                health["issues"].append("Cannot write to base directory")
                health["writable"] = False
            
            # Set overall status
            if health["issues"]:
                health["status"] = "unhealthy"
            
            return health
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "directories_exist": False,
                "writable": False
            }
    
    def apply_shared_metadata(
        self,
        resource_data: Dict[str, Any],
        resource_id: str,
        resource_type: str,
        user_id: Optional[str]
    ) -> Dict[str, Any]:
        """
        Apply is_shared and owner_id metadata to a resource based on deployment mode.
        
        This ensures consistent behavior across all resource types:
        - Self-hosted mode: is_shared=False (all resources editable)
        - Public mode: is_shared based on storage location
        
        Args:
            resource_data: The resource data dict to modify
            resource_id: ID of the resource
            resource_type: Type of resource (plugins, boxes, etc.)
            user_id: User ID (None for self-hosted mode)
            
        Returns:
            Modified resource_data with is_shared and owner_id fields set
        """
        if user_id is None:
            # Self-hosted mode: all resources are editable
            resource_data["is_shared"] = False
            resource_data["owner_id"] = None
        else:
            # Public mode: check if resource is in shared directory
            shared_path = self.get_shared_data_path(resource_type) / f"{resource_id}.json"
            user_path = self.get_user_data_path(user_id, resource_type) / f"{resource_id}.json"
            
            if user_path.exists():
                # User's own resource
                resource_data["is_shared"] = False
                resource_data["owner_id"] = user_id
            elif shared_path.exists():
                # Shared resource
                resource_data["is_shared"] = True
                resource_data["owner_id"] = None
        
        return resource_data