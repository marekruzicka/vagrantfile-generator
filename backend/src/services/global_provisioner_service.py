"""
Global Provisioner Service for Vagrantfile GUI Generator.

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


class GlobalProvisionerServiceError(Exception):
    """Custom exception for global provisioner service errors."""
    pass


class GlobalProvisionerService:
    """Service for handling global provisioner operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the global provisioner service.
        
        Args:
            base_directory: Base directory for storing provisioner files
        """
        self.base_directory = Path(base_directory)
        self.provisioners_directory = self.base_directory / "provisioners"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
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
            Provisioner if found, None otherwise
        """
        try:
            provisioner_data = self._load_provisioner_from_file(provisioner_id)
            
            if not provisioner_data:
                return None
            
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
            GlobalProvisionerServiceError: If provisioner name conflicts with another provisioner
        """
        try:
            existing_data = self._load_provisioner_from_file(provisioner_id)
            
            if not existing_data:
                return None
            
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
        """
        try:
            file_path = self._get_provisioner_file_path(provisioner_id)
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to delete provisioner: {str(e)}")
    
    def list_provisioners(self, include_deprecated: bool = True) -> List[GlobalProvisioner]:
        """
        List all provisioners.
        
        Args:
            include_deprecated: Whether to include deprecated provisioners
            
        Returns:
            List of provisioners
        """
        try:
            all_ids = self._list_all_provisioner_ids()
            provisioners = []
            
            for provisioner_id in all_ids:
                provisioner_data = self._load_provisioner_from_file(provisioner_id)
                if provisioner_data:
                    try:
                        provisioner = GlobalProvisioner(**provisioner_data)
                        provisioners.append(provisioner)
                    except Exception as e:
                        # Log error but continue with other provisioners
                        print(f"Warning: Failed to parse provisioner {provisioner_id}: {e}")
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
                    scope=p.scope
                )
                for p in provisioners
            ]
            
        except Exception as e:
            raise GlobalProvisionerServiceError(f"Failed to list provisioner summaries: {str(e)}")
