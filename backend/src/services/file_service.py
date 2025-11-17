"""
FileService for Vagrantfile Generator.

This service handles file I/O operations for multi-user data storage.
"""

import json
import os
import time
import fcntl
import tempfile
from typing import Dict, List, Any, Optional
from pathlib import Path
from contextlib import contextmanager


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
        return resource_data
    
    def atomic_write_json(self, file_path: Path, data: dict) -> None:
        """
        Write JSON data atomically using temp file + rename.
        
        On Unix systems, os.replace() is atomic, ensuring readers never
        see partial/corrupted data.
        
        Args:
            file_path: Path to file to write
            data: Dictionary to serialize as JSON
            
        Raises:
            FileServiceError: If write operation fails
        """
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create temp file in same directory (same filesystem for atomic rename)
        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=f".tmp_{file_path.name}_",
            suffix='.json'
        )
        
        try:
            # Write to temp file
            with os.fdopen(fd, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
            
            # Atomic rename (on Unix, this is atomic even across processes)
            os.replace(temp_path, file_path)
            
        except Exception as e:
            # Cleanup temp file on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise FileServiceError(f"Atomic write failed for {file_path}: {e}")
    
    @contextmanager
    def locked_file_operation(
        self, 
        file_path: Path, 
        mode: str = 'exclusive',
        timeout: float = 5.0
    ):
        """
        Context manager for locked file operations.
        
        Provides advisory file locking to prevent concurrent modifications.
        Uses a separate .lock file to avoid interfering with the data file.
        
        Args:
            file_path: Path to file to lock
            mode: 'exclusive' (write) or 'shared' (read)
            timeout: Maximum seconds to wait for lock
            
        Usage:
            with file_service.locked_file_operation(path, 'exclusive'):
                data = load_file(path)
                modify_data(data)
                save_file(path, data)
                
        Raises:
            FileServiceError: If lock cannot be acquired within timeout
        """
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create lock file (separate from data file)
        lock_file_path = file_path.parent / f".{file_path.name}.lock"
        
        lock_fd = None
        lock_acquired = False
        
        try:
            # Open lock file
            lock_fd = os.open(
                lock_file_path, 
                os.O_CREAT | os.O_RDWR
            )
            
            # Determine lock type
            lock_type = fcntl.LOCK_EX if mode == 'exclusive' else fcntl.LOCK_SH
            
            # Try to acquire lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd, lock_type | fcntl.LOCK_NB)
                    lock_acquired = True
                    break
                except BlockingIOError:
                    if time.time() - start_time >= timeout:
                        raise FileServiceError(
                            f"Could not acquire lock on {file_path.name} "
                            f"within {timeout} seconds"
                        )
                    time.sleep(0.01)  # Wait 10ms before retry
            
            # Yield control to caller (lock is held)
            yield
            
        finally:
            # Release lock
            if lock_acquired and lock_fd is not None:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                except:
                    pass
            
            # Close lock file descriptor
            if lock_fd is not None:
                try:
                    os.close(lock_fd)
                except:
                    pass
