"""
Global Trigger Service for Vagrantfile Generator.

This service handles CRUD operations for global triggers.
Follows the same file-based pattern as the provisioner service.
"""

import json
import uuid
from typing import List, Optional
from pathlib import Path
from datetime import datetime

from ..models.global_trigger import (
    GlobalTrigger,
    GlobalTriggerCreate,
    GlobalTriggerUpdate,
    GlobalTriggerSummary
)
from .file_service import FileService


class GlobalTriggerServiceError(Exception):
    """Custom exception for global trigger service errors."""
    pass


class GlobalTriggerService:
    """Service for handling global trigger operations."""
    
    def __init__(self, base_directory: str = "data", user_id: Optional[str] = None, show_shared: Optional[bool] = None):
        """
        Initialize the global trigger service.
        
        Args:
            base_directory: Base directory for storing trigger files (deprecated, use user_id)
            user_id: User ID for user-specific storage. If None, uses shared directory.
            show_shared: Override for show_shared_resources preference (for testing)
        """
        # Support user-specific directories
        if user_id:
            file_service = FileService()
            self.triggers_directory = file_service.get_user_data_path(user_id, "triggers")
        else:
            # For backward compatibility and self-hosted mode
            if base_directory == "data":
                # Use shared directory in new multi-user setup
                file_service = FileService()
                self.triggers_directory = file_service.get_shared_data_path("triggers")
            else:
                # Legacy direct path specification
                self.base_directory = Path(base_directory)
                self.triggers_directory = self.base_directory / "triggers"
        
        self.user_id = user_id
        self.file_service = FileService()
        self.data_dir = self.triggers_directory  # Alias for backwards compatibility
        
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
        self.triggers_directory.mkdir(parents=True, exist_ok=True)
    
    def _get_trigger_file_path(self, trigger_id: str) -> Path:
        """Get the file path for a specific trigger."""
        return self.triggers_directory / f"{trigger_id}.json"
    
    def _load_trigger_from_file(self, trigger_id: str) -> Optional[dict]:
        """Load a trigger from its JSON file."""
        try:
            file_path = self._get_trigger_file_path(trigger_id)
            
            # Try user directory first, then shared directory
            if not file_path.exists() and self.user_id:
                file_service = FileService()
                shared_path = file_service.get_shared_data_path("triggers") / f"{trigger_id}.json"
                if shared_path.exists():
                    file_path = shared_path
            
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to load trigger {trigger_id}: {str(e)}")
    
    def _save_trigger_to_file(self, trigger_data: dict):
        """Save a trigger to its JSON file."""
        try:
            trigger_id = trigger_data.get("id")
            if not trigger_id:
                raise GlobalTriggerServiceError("Trigger data missing 'id' field")
            
            file_path = self._get_trigger_file_path(trigger_id)
            
            # Update timestamp
            trigger_data["updated_at"] = datetime.now().isoformat()

            # Ensure metadata fields exist in stored JSON
            if "is_shared" not in trigger_data:
                trigger_data["is_shared"] = False
            if "owner_id" not in trigger_data:
                trigger_data["owner_id"] = self.user_id if self.user_id else None
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(trigger_data, f, indent=2, ensure_ascii=False)
                
        except GlobalTriggerServiceError:
            raise
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to save trigger: {str(e)}")
    
    def _list_all_trigger_ids(self) -> List[str]:
        """List all trigger IDs from the directory."""
        try:
            if not self.triggers_directory.exists():
                return []
            
            trigger_files = self.triggers_directory.glob("*.json")
            return [f.stem for f in trigger_files]
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to list triggers: {str(e)}")
    
    def _check_name_conflict(self, name: str, exclude_id: Optional[str] = None) -> bool:
        """
        Check if a trigger with the given name already exists.
        
        Args:
            name: Trigger name to check
            exclude_id: Trigger ID to exclude from check (for updates)
            
        Returns:
            True if conflict exists, False otherwise
        """
        try:
            all_ids = self._list_all_trigger_ids()
            
            for trigger_id in all_ids:
                if exclude_id and trigger_id == exclude_id:
                    continue
                
                trigger_data = self._load_trigger_from_file(trigger_id)
                if trigger_data and trigger_data.get("name") == name:
                    return True
            
            return False
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to check name conflict: {str(e)}")
    
    def create_trigger(self, trigger_data: GlobalTriggerCreate) -> GlobalTrigger:
        """
        Create a new global trigger.
        
        Args:
            trigger_data: Trigger creation data
            
        Returns:
            Created trigger
            
        Raises:
            GlobalTriggerServiceError: If trigger with same name already exists
        """
        try:
            # Check if trigger with same name already exists
            if self._check_name_conflict(trigger_data.name):
                raise GlobalTriggerServiceError(
                    f"Trigger with name '{trigger_data.name}' already exists"
                )
            
            # Create new trigger
            now = datetime.now().isoformat()
            new_trigger = {
                "id": str(uuid.uuid4()),
                "name": trigger_data.name,
                "description": trigger_data.description,
                "trigger_config": trigger_data.trigger_config.model_dump(),
                "is_shared": False,
                "owner_id": self.user_id if self.user_id else None,
                "created_at": now,
                "updated_at": now
            }
            
            # Save to file
            self._save_trigger_to_file(new_trigger)
            
            # Return as model
            return GlobalTrigger(**new_trigger)
            
        except GlobalTriggerServiceError:
            raise
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to create trigger: {str(e)}")
    
    def get_trigger(self, trigger_id: str) -> Optional[GlobalTrigger]:
        """
        Get a specific trigger by ID.
        
        Args:
            trigger_id: Trigger ID
            
        Returns:
            Trigger if found and user has access, None otherwise
        """
        try:
            trigger_data = self._load_trigger_from_file(trigger_id)
            
            if not trigger_data:
                return None
            
            # Apply is_shared and owner_id metadata
            trigger_data = self.file_service.apply_shared_metadata(
                trigger_data, trigger_id, "triggers", self.user_id
            )
            
            return GlobalTrigger(**trigger_data)
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to get trigger: {str(e)}")
    
    def list_triggers(self) -> List[GlobalTrigger]:
        """
        List all triggers (merged shared + user-specific).
        Filters based on show_shared_resources preference.
        
        Returns:
            List of GlobalTrigger instances with is_shared and owner_id fields
        """
        try:
            file_service = FileService()
            
            # Loader function for merge_resources
            def load_trigger_data(file_path: Path) -> dict:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Merge shared and user resources
            merged_data = file_service.merge_resources(
                user_id=self.user_id,
                resource_type="triggers",
                loader_func=load_trigger_data
            )
            
            triggers = []
            
            # Load favorites if user is authenticated
            favorite_ids = []
            if self.user_id:
                from .preference_service import PreferenceService
                pref_service = PreferenceService(self.user_id)
                favorite_ids = pref_service.get_favorites('triggers')
            
            for trigger_data in merged_data:
                trigger = GlobalTrigger(**trigger_data)
                
                # Filter based on preferences
                # Show resource if: not shared, OR show_shared=True, OR is a favorite
                if trigger.is_shared and not self.show_shared and trigger.id not in favorite_ids:
                    continue
                
                triggers.append(trigger)
            
            # Sort by name
            triggers.sort(key=lambda t: t.name.lower())
            
            return triggers
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to list triggers: {str(e)}")
    
    def list_triggers_summary(self) -> List[GlobalTriggerSummary]:
        """
        List all triggers as summaries (for display in lists).
        
        Returns:
            List of trigger summaries
        """
        try:
            triggers = self.list_triggers()
            return [
                GlobalTriggerSummary(
                    id=t.id,
                    name=t.name,
                    description=t.description,
                    timing=t.trigger_config.timing,
                    stage=t.trigger_config.stage,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    is_shared=t.is_shared,
                    owner_id=t.owner_id
                )
                for t in triggers
            ]
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to list trigger summaries: {str(e)}")
    
    def copy_shared_trigger(self, trigger_id: str) -> GlobalTrigger:
        """
        Create a copy of a shared trigger in user's directory.
        User can then edit/customize their copy.
        
        Args:
            trigger_id: ID of the shared trigger to copy
            
        Returns:
            Copied trigger with new ID
            
        Raises:
            GlobalTriggerServiceError: If trigger not found, not shared, or user_id not set
        """
        if not self.user_id:
            raise GlobalTriggerServiceError("Cannot copy triggers in self-hosted mode")
        
        try:
            # Load shared trigger
            shared_file = self.file_service.get_shared_data_path("triggers") / f"{trigger_id}.json"
            
            if not shared_file.exists():
                raise GlobalTriggerServiceError(f"Shared trigger {trigger_id} not found")
            
            with open(shared_file, 'r', encoding='utf-8') as f:
                trigger_data = json.load(f)
            
            # Verify it's a shared resource
            if not trigger_data.get("is_shared", False):
                raise GlobalTriggerServiceError("Can only copy shared resources")
            
            # Generate new ID for the copy
            new_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create copy with new metadata
            trigger_copy = {
                **trigger_data,
                "id": new_id,
                "name": f"{trigger_data['name']} (Copy)",
                "is_shared": False,
                "owner_id": self.user_id,
                "source_id": trigger_id,  # Track original shared resource
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory
            user_file = self.file_service.get_user_data_path(self.user_id, "triggers") / f"{new_id}.json"
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(trigger_copy, f, indent=2, ensure_ascii=False)
            
            return GlobalTrigger(**trigger_copy)
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to copy trigger: {str(e)}")
    
    def update_trigger(self, trigger_id: str, update_data: GlobalTriggerUpdate) -> GlobalTrigger:
        """
        Update an existing trigger.
        
        Args:
            trigger_id: Trigger ID to update
            update_data: Updated trigger data
            
        Returns:
            Updated trigger
            
        Raises:
            GlobalTriggerServiceError: If trigger not found, name conflict, or trying to edit shared resource
        """
        try:
            # Load existing trigger
            existing_data = self._load_trigger_from_file(trigger_id)
            if not existing_data:
                raise GlobalTriggerServiceError(f"Trigger with ID {trigger_id} not found")
            
            # Check if trying to edit a shared resource in public mode
            if self.user_id:
                user_file = self.data_dir / f"{trigger_id}.json"
                if not user_file.exists():
                    raise GlobalTriggerServiceError("Cannot edit shared resources")
            
            # Check name conflict (excluding current trigger)
            if self._check_name_conflict(update_data.name, exclude_id=trigger_id):
                raise GlobalTriggerServiceError(
                    f"Trigger with name '{update_data.name}' already exists"
                )
            
            # Update data
            updated_data = {
                "id": trigger_id,
                "name": update_data.name,
                "description": update_data.description,
                "trigger_config": update_data.trigger_config.model_dump(),
                "created_at": existing_data.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat()
            }
            
            # Save to file
            self._save_trigger_to_file(updated_data)
            
            # Return as model
            return GlobalTrigger(**updated_data)
            
        except GlobalTriggerServiceError:
            raise
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to update trigger: {str(e)}")
    
    def delete_trigger(self, trigger_id: str) -> bool:
        """
        Delete a trigger.
        
        Args:
            trigger_id: Trigger ID to delete
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            GlobalTriggerServiceError: If trying to delete shared resource
        """
        try:
            # Check if trying to delete a shared resource in public mode
            if self.user_id:
                user_file = self.data_dir / f"{trigger_id}.json"
                if not user_file.exists():
                    raise GlobalTriggerServiceError("Cannot delete shared resources")
            
            file_path = self._get_trigger_file_path(trigger_id)
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to delete trigger: {str(e)}")
    
    def copy_shared_trigger(self, trigger_id: str) -> GlobalTrigger:
        """
        Create a copy of a shared trigger in user's directory.
        User can then edit/customize their copy.
        
        Args:
            trigger_id: ID of the shared trigger to copy
            
        Returns:
            Copied trigger with new ID
            
        Raises:
            GlobalTriggerServiceError: If trigger not found, not shared, or user_id not set
        """
        if not self.user_id:
            raise GlobalTriggerServiceError("Cannot copy triggers in self-hosted mode")
        
        try:
            # Load shared trigger
            shared_file = self.file_service.get_shared_data_path("triggers") / f"{trigger_id}.json"
            
            if not shared_file.exists():
                raise GlobalTriggerServiceError(f"Shared trigger {trigger_id} not found")
            
            with open(shared_file, 'r', encoding='utf-8') as f:
                trigger_data = json.load(f)
            
            # Verify it's a shared resource
            if not trigger_data.get("is_shared", False):
                raise GlobalTriggerServiceError("Can only copy shared resources")
            
            # Generate new ID for the copy
            new_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create copy with new metadata
            trigger_copy = {
                **trigger_data,
                "id": new_id,
                "name": f"{trigger_data['name']} (Copy)",
                "is_shared": False,
                "owner_id": self.user_id,
                "source_id": trigger_id,  # Track original shared resource
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory
            user_file = self.file_service.get_user_data_path(self.user_id, "triggers") / f"{new_id}.json"
            with open(user_file, 'w', encoding='utf-8') as f:
                json.dump(trigger_copy, f, indent=2, ensure_ascii=False)
            
            return GlobalTrigger(**trigger_copy)
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to copy trigger: {str(e)}")
    
    def get_copies_of_shared_resource(self, source_id: str) -> List[GlobalTrigger]:
        """
        Get all user's copies of a specific shared resource.
        
        Args:
            source_id: ID of the original shared resource
            
        Returns:
            List of triggers that were copied from the specified shared resource
            
        Raises:
            GlobalTriggerServiceError: If user_id not set
        """
        if not self.user_id:
            return []  # Self-hosted mode has no copies
        
        try:
            # List all user triggers and filter by source_id
            all_triggers = self.list_triggers()
            copies = [t for t in all_triggers if t.source_id == source_id]
            return copies
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to get copies: {str(e)}")
