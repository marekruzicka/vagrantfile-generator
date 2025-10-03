"""
Global Trigger Service for Vagrantfile GUI Generator.

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


class GlobalTriggerServiceError(Exception):
    """Custom exception for global trigger service errors."""
    pass


class GlobalTriggerService:
    """Service for handling global trigger operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the global trigger service.
        
        Args:
            base_directory: Base directory for storing trigger files
        """
        self.base_directory = Path(base_directory)
        self.triggers_directory = self.base_directory / "triggers"
        
        # Create directories if they don't exist
        self._ensure_directories()
    
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
            Trigger if found, None otherwise
        """
        try:
            trigger_data = self._load_trigger_from_file(trigger_id)
            
            if not trigger_data:
                return None
            
            return GlobalTrigger(**trigger_data)
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to get trigger: {str(e)}")
    
    def list_triggers(self) -> List[GlobalTrigger]:
        """
        List all global triggers.
        
        Returns:
            List of triggers
        """
        try:
            all_ids = self._list_all_trigger_ids()
            triggers = []
            
            for trigger_id in all_ids:
                trigger_data = self._load_trigger_from_file(trigger_id)
                if trigger_data:
                    try:
                        triggers.append(GlobalTrigger(**trigger_data))
                    except Exception as e:
                        # Log error but continue with other triggers
                        print(f"Warning: Failed to load trigger {trigger_id}: {str(e)}")
            
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
                    updated_at=t.updated_at
                )
                for t in triggers
            ]
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to list trigger summaries: {str(e)}")
    
    def update_trigger(self, trigger_id: str, update_data: GlobalTriggerUpdate) -> GlobalTrigger:
        """
        Update an existing trigger.
        
        Args:
            trigger_id: Trigger ID to update
            update_data: Updated trigger data
            
        Returns:
            Updated trigger
            
        Raises:
            GlobalTriggerServiceError: If trigger not found or name conflict
        """
        try:
            # Load existing trigger
            existing_data = self._load_trigger_from_file(trigger_id)
            if not existing_data:
                raise GlobalTriggerServiceError(f"Trigger with ID {trigger_id} not found")
            
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
        """
        try:
            file_path = self._get_trigger_file_path(trigger_id)
            
            if not file_path.exists():
                return False
            
            file_path.unlink()
            return True
            
        except Exception as e:
            raise GlobalTriggerServiceError(f"Failed to delete trigger: {str(e)}")
