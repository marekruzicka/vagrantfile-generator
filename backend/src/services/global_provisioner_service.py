"""
Global Provisioner Service for Vagrantfile Generator.

This service handles CRUD operations for global provisioners.
Follows the same file-based pattern as the plugin service.
"""

import json
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ..models.global_provisioner import (
    GlobalProvisioner,
    GlobalProvisionerCreate,
    GlobalProvisionerUpdate,
    GlobalProvisionerSummary
)
from .file_service import FileService


class GlobalProvisionerServiceError(Exception):
    """Custom exception for global provisioner service errors."""
    pass


class GlobalProvisionerService:
    """Service for handling global provisioner operations."""
    
    def __init__(self, base_directory: str = "data", user_id: Optional[str] = None, show_shared: Optional[bool] = None):
        """
        Initialize the global provisioner service.
        
        Args:
            base_directory: Base directory for storing provisioner files (deprecated, use user_id)
            user_id: User ID for user-specific storage. If None, uses shared directory.
            show_shared: Override for show_shared_resources preference (for testing)
        """
        # Support user-specific directories
        if user_id:
            file_service = FileService()
            self.provisioners_directory = file_service.get_user_data_path(user_id, "provisioners")
        else:
            # For backward compatibility and self-hosted mode
            if base_directory == "data":
                # Use shared directory in new multi-user setup
                file_service = FileService()
                self.provisioners_directory = file_service.get_shared_data_path("provisioners")
            else:
                # Legacy direct path specification
                self.base_directory = Path(base_directory)
                self.provisioners_directory = self.base_directory / "provisioners"
        
        self.user_id = user_id
        self.file_service = FileService()
        self.data_dir = self.provisioners_directory  # Alias for backwards compatibility
        
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
        self.provisioners_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_provisioner_file_path(self, provisioner_id: str) -> Path:
        """Get the file path for a specific provisioner."""
        return self.provisioners_directory / f"{provisioner_id}.json"
    
    def _load_provisioner_from_file(self, provisioner_id: str) -> Optional[dict]:
        """Load a provisioner from its JSON file."""
        try:
            file_path = self._get_provisioner_file_path(provisioner_id)
            
            # Try user directory first, then shared directory
            if not file_path.exists() and self.user_id:
                file_service = FileService()
                shared_path = file_service.get_shared_data_path("provisioners") / f"{provisioner_id}.json"
                if shared_path.exists():
                    file_path = shared_path
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to load provisioner {provisioner_id}: {str(e)}")
    
    def _save_provisioner_to_file(self, provisioner_data: dict):
        """Save a provisioner to its JSON file."""
        try:
            provisioner_id = provisioner_data.get("id")
            if not provisioner_id:
                raise GlobalProvisionerServiceError("Provisioner data missing 'id' field")
            
            file_path = self._get_provisioner_file_path(provisioner_id)
            
            # Update timestamp
            provisioner_data["updated_at"] = datetime.now().isoformat()
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(provisioner_data, f, indent=2, ensure_ascii=False)
                
        except GlobalProvisionerServiceError:
            raise
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to save provisioner: {str(e)}")
    
    def _list_all_provisioner_ids(self) -> List[str]:
        """List all provisioner IDs from the directory."""
        try:
            if not self.provisioners_directory.exists():
                return []
            
            provisioner_files = self.provisioners_directory.glob("*.json")
            return [f.stem for f in provisioner_files]
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to list provisioners: {str(e)}")
    
    def _check_name_conflict(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if a provisioner with the given name already exists.
        
        Args:
            name: Provisioner name to check
            exclude_id: Provisioner ID to exclude from check (for updates)
            
        Returns:
            True if conflict exists, False otherwise
        """
        try:
            all_ids = self._list_all_provisioner_ids()
            
            for provisioner_id in all_ids:
                if exclude_id and provisioner_id == exclude_id:
                    continue
                
                provisioner_data = self._load_provisioner_from_file(provisioner_id)
                if provisioner_data and provisioner_data.get("name") == name:
                    return True
            
            return False
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to check name conflict: {str(e)}")
    
    def create_provisioner(self, provisioner_data: GlobalProvisionerCreate) -> GlobalProvisioner:
        """
        Create a new global provisioner.
        
        Args:
            provisioner_data: Provisioner creation data
            
        Returns:
            Created provisioner
            
        Raises:
            GlobalProvisionerServiceError: If provisioner with same name already exists
        """
        try:
            # Check if provisioner with same name already exists
            if self._check_name_conflict(provisioner_data.name):
                raise GlobalProvisionerServiceError(
                    f"Provisioner with name '{provisioner_data.name}' already exists"
                )
            
            # Create new provisioner
            now = datetime.now().isoformat()
            new_provisioner = {
                "id": str(uuid.uuid4()),
                "name": provisioner_data.name,
                "description": provisioner_data.description,
                "type": provisioner_data.type,
                "scope": provisioner_data.scope,
                "shell_config": provisioner_data.shell_config.model_dump() if provisioner_data.shell_config else None,
                "created_at": now,
                "updated_at": now
            }
            
            self._save_provisioner_to_file(new_provisioner)
            
            return GlobalProvisioner(**new_provisioner)
            
        except GlobalProvisionerServiceError:
            raise
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to create provisioner: {str(e)}")
    
    def get_provisioner(self, provisioner_id: str) -> Optional[GlobalProvisioner]:
        """
        Get a specific provisioner by ID.
        
        Args:
            provisioner_id: Provisioner ID to retrieve
            
        Returns:
            Provisioner if found and user has access, None otherwise
        """
        try:
            provisioner_data = self._load_provisioner_from_file(provisioner_id)
            
            if not provisioner_data:
                return None
            
            # In public mode (user_id set), access control is enforced by directory structure
            # If file is found in user's directory, access is allowed
            return GlobalProvisioner(**provisioner_data)
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to get provisioner: {str(e)}")
    
    def get_provisioner_by_name(self, provisioner_name: str) -> Optional[GlobalProvisioner]:
        """
        Get a specific provisioner by name.
        
        Args:
            provisioner_name: Provisioner name to retrieve
            
        Returns:
            Provisioner if found, None otherwise
        """
        try:
            all_ids = self._list_all_provisioner_ids()
            
            for provisioner_id in all_ids:
                provisioner_data = self._load_provisioner_from_file(provisioner_id)
                if provisioner_data and provisioner_data.get("name") == provisioner_name:
                    return GlobalProvisioner(**provisioner_data)
            
            return None
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to get provisioner by name: {str(e)}")
    
    def update_provisioner(
        self,
        provisioner_id: str,
        provisioner_data: GlobalProvisionerUpdate
    ) -> Optional[GlobalProvisioner]:
        """
        Update an existing provisioner.
        
        Args:
            provisioner_id: Provisioner ID to update
            provisioner_data: Provisioner update data
            
        Returns:
            Updated provisioner if found, None otherwise
            
        Raises:
            GlobalProvisionerServiceError: If provisioner name conflicts or trying to edit shared resource
        """
        try:
            existing_data = self._load_provisioner_from_file(provisioner_id)
            
            if not existing_data:
                return None
            
            # Check if trying to edit a shared resource in public mode
            if self.user_id:
                user_file = self.data_dir / f"{provisioner_id}.json"
                if not user_file.exists():
                    raise GlobalProvisionerServiceError("Cannot edit shared resources")
            
            # Check for name conflicts if name is being updated
            if provisioner_data.name and provisioner_data.name != existing_data.get("name"):
                if self._check_name_conflict(provisioner_data.name, exclude_id=provisioner_id):
                    raise GlobalProvisionerServiceError(
                        f"Provisioner with name '{provisioner_data.name}' already exists"
                    )
            
            # Update provisioner fields
            update_dict = provisioner_data.model_dump(exclude_unset=True)
            
            for key, value in update_dict.items():
                if value is not None:
                    if key == "shell_config" and value:
                        existing_data[key] = value
                    else:
                        existing_data[key] = value
            
            self._save_provisioner_to_file(existing_data)
            
            return GlobalProvisioner(**existing_data)
            
        except GlobalProvisionerServiceError:
            raise
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to update provisioner: {str(e)}")
    
    def delete_provisioner(self, provisioner_id: str) -> bool:
        """
        Delete a provisioner.
        
        Args:
            provisioner_id: Provisioner ID to delete
            
        Returns:
            True if provisioner was deleted, False if not found
            
        Raises:
            GlobalProvisionerServiceError: If trying to delete shared resource
        """
        try:
            # Check if trying to delete a shared resource in public mode
            if self.user_id:
                user_file = self.data_dir / f"{provisioner_id}.json"
                if not user_file.exists():
                    raise GlobalProvisionerServiceError("Cannot delete shared resources")
            
            file_path = self._get_provisioner_file_path(provisioner_id)
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to delete provisioner: {str(e)}")
    
    def list_provisioners(self, include_deprecated: bool = True) -> List[GlobalProvisioner]:
        """
        List all provisioners (merged shared + user-specific).
        Filters based on show_shared_resources preference.
        
        Args:
            include_deprecated: Whether to include deprecated provisioners
            
        Returns:
            List of provisioners with is_shared and owner_id fields
        """
        try:
            file_service = FileService()
            
            # Loader function for merge_resources
            def load_provisioner_data(file_path: Path) -> dict:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Merge shared and user resources
            merged_data = file_service.merge_resources(
                user_id=self.user_id,
                resource_type="provisioners",
                loader_func=load_provisioner_data
            )
            
            provisioners = []
            
            # Load favorites if user is authenticated
            favorite_ids = []
            if self.user_id:
                from .preference_service import PreferenceService
                pref_service = PreferenceService(self.user_id)
                favorite_ids = pref_service.get_favorites('provisioners')
            
            for provisioner_data in merged_data:
                try:
                    provisioner = GlobalProvisioner(**provisioner_data)
                    
                    # Filter based on preferences
                    # Show resource if: not shared, OR show_shared=True, OR is a favorite
                    if provisioner.is_shared and not self.show_shared and provisioner.id not in favorite_ids:
                        continue
                    
                    provisioners.append(provisioner)
                except Exception as e:
                    # Log error but continue with other provisioners
                    print(f"Warning: Failed to parse provisioner: {e}")
                    continue
            
            # Sort by name
            provisioners.sort(key=lambda p: p.name.lower())
            
            return provisioners
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to list provisioners: {str(e)}")
    
    def list_provisioners_summary(self, include_deprecated: bool = True) -> List[GlobalProvisionerSummary]:
        """
        List all provisioners as summaries.
        
        Args:
            include_deprecated: Whether to include deprecated provisioners
            
        Returns:
            List of provisioner summaries
        """
        try:
            provisioners = self.list_provisioners(include_deprecated)
            
            return [
                GlobalProvisionerSummary(
                    id=p.id,
                    name=p.name,
                    description=p.description,
                    type=p.type,
                    scope=p.scope,
                    is_shared=p.is_shared,
                    owner_id=p.owner_id
                )
                for p in provisioners
            ]
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to list provisioner summaries: {str(e)}")
    
    def copy_shared_provisioner(self, provisioner_id: str) -> GlobalProvisioner:
        """
        Create a copy of a shared provisioner in user's directory.
        User can then edit/customize their copy.
        
        Args:
            provisioner_id: ID of the shared provisioner to copy
            
        Returns:
            Copied provisioner with new ID
            
        Raises:
            GlobalProvisionerServiceError: If provisioner not found, not shared, or user_id not set
        """
        if not self.user_id:
            raise GlobalProvisionerServiceError("Cannot copy provisioners in self-hosted mode")
        
        try:
            # Load shared provisioner
            shared_file = self.file_service.get_shared_data_path("provisioners") / f"{provisioner_id}.json"
            
            if not shared_file.exists():
                raise GlobalProvisionerServiceError(f"Shared provisioner {provisioner_id} not found")
            
            with open(shared_file, 'r', encoding='utf-8') as f:
                provisioner_data = json.load(f)
            
            # Verify it's a shared resource
            if not provisioner_data.get("is_shared", False):
                raise GlobalProvisionerServiceError("Can only copy shared resources")
            
            # Generate new ID for the copy
            new_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create copy with new metadata
            provisioner_copy = {
                **provisioner_data,
                "id": new_id,
                "name": f"{provisioner_data['name']} (Copy)",
                "is_shared": False,
                "owner_id": self.user_id,
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory
            user_file = self.file_service.get_user_data_path(self.user_id, "provisioners") / f"{new_id}.json"
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(provisioner_copy, f, indent=2, ensure_ascii=False)
            
            return GlobalProvisioner(**provisioner_copy)
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to copy provisioner: {str(e)}")
