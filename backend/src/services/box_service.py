"""
BoxService for Vagrantfile Generator.

This service handles CRUD operations for Vagrant box configurations.
"""

import os
import json
import uuid
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime

from ..models.box import Box, BoxCreate, BoxUpdate, BoxSummary
from .file_service import FileService


class BoxServiceError(Exception):
    """Custom exception for box service errors."""
    pass


class BoxService:
    """Service for handling box operations."""
    
    def __init__(self, base_directory: str = "data", user_id: Optional[str] = None, show_shared: Optional[bool] = None):
        """
        Initialize the box service.
        
        Args:
            base_directory: Base directory for storing box files (deprecated, use user_id)
            user_id: User ID for user-specific storage. If None, uses shared directory.
            show_shared: Override for show_shared_resources preference (for testing)
        """
        self.file_service = FileService()
        self.user_id = user_id
        
        # Support user-specific directories
        if user_id:
            self.boxes_directory = self.file_service.get_user_data_path(user_id, "boxes")
        else:
            # For backward compatibility and self-hosted mode
            if base_directory == "data":
                # Use shared directory in new multi-user setup
                self.boxes_directory = self.file_service.get_shared_data_path("boxes")
            else:
                # Legacy direct path specification
                self.base_directory = Path(base_directory)
                self.boxes_directory = self.base_directory / "boxes"
        
        # Load show_shared preference
        if show_shared is not None:
            self.show_shared = show_shared
        else:
            self.show_shared = self._load_show_shared_preference()
        
        # Create directories if they don't exist
        self.boxes_directory.mkdir(parents=True, exist_ok=True)
    
    def _load_show_shared_preference(self) -> bool:
        """Load user's preference for showing shared resources."""
        if not self.user_id:
            return True  # Self-hosted mode: always show shared
        
        from .preference_service import PreferenceService
        pref_service = PreferenceService(self.user_id)
        return pref_service.get_show_shared_resources()
    
    def create_box(self, box_data: BoxCreate) -> Box:
        """
        Create a new box.
        
        Args:
            box_data: Box creation data
            
        Returns:
            Created box
            
        Raises:
            BoxServiceError: If creation fails
        """
        try:
            # Check if box name already exists
            existing_boxes = self.list_boxes()
            if any(box.name == box_data.name for box in existing_boxes):
                raise BoxServiceError(f"Box with name '{box_data.name}' already exists")
            
            # Create new box
            box_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            box_dict = {
                "id": box_id,
                "name": box_data.name,
                "description": box_data.description,
                "provider": box_data.provider,
                "version": box_data.version,
                "url": box_data.url,
                "is_shared": False,
                "owner_id": self.user_id if self.user_id else None,
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory if in public mode
            if self.user_id:
                file_path = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
            else:
                file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
            
            self.file_service.atomic_write_json(file_path, box_dict)
            
            return Box(**box_dict)
            
        except BoxServiceError:
            raise
        except Exception as e:
            raise BoxServiceError(f"Failed to create box: {str(e)}")
    
    def get_box(self, box_id: str) -> Optional[Box]:
        """
        Get a box by ID.
        
        Args:
            box_id: Box ID
            
        Returns:
            Box if found, None otherwise
        """
        try:
            box_data = None
            
            # Try user directory first
            if self.user_id:
                user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
                if user_file.exists():
                    with open(user_file, 'r', encoding='utf-8') as f:
                        box_data = json.load(f)
            
            # Try shared directory if not found in user directory
            if not box_data:
                shared_file = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
                if shared_file.exists():
                    with open(shared_file, 'r', encoding='utf-8') as f:
                        box_data = json.load(f)
            
            if not box_data:
                return None
            
            # Apply is_shared and owner_id metadata
            box_data = self.file_service.apply_shared_metadata(
                box_data, box_id, "boxes", self.user_id
            )
            
            return Box(**box_data)
            
        except Exception as e:
            raise BoxServiceError(f"Failed to get box {box_id}: {str(e)}")
    
    def update_box(self, box_id: str, box_data: BoxUpdate) -> Optional[Box]:
        """
        Update an existing box.
        
        Args:
            box_id: Box ID
            box_data: Box update data
            
        Returns:
            Updated box if found, None otherwise
            
        Raises:
            BoxServiceError: If update fails or trying to edit shared resource
        """
        try:
            # Prevent editing shared resources in public mode
            if self.user_id:
                user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
                if not user_file.exists():
                    raise BoxServiceError("Cannot edit shared resources")
                file_path = user_file
            else:
                file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
            
            if not file_path.exists():
                return None
            
            # Load existing box
            with open(file_path, 'r', encoding='utf-8') as f:
                box_dict = json.load(f)
            
            # Check if name is being changed and doesn't conflict
            if box_data.name and box_data.name != box_dict['name']:
                existing_boxes = self.list_boxes()
                if any(box.name == box_data.name and box.id != box_id for box in existing_boxes):
                    raise BoxServiceError(f"Box with name '{box_data.name}' already exists")
            
            # Update fields - handle optional fields specially
            if box_data.name is not None:
                box_dict['name'] = box_data.name
            if box_data.description is not None:
                box_dict['description'] = box_data.description
            if box_data.provider is not None:
                box_dict['provider'] = box_data.provider
            
            # For optional fields, update if explicitly provided (including None)
            update_data = box_data.dict(exclude_unset=True)
            if 'version' in update_data:
                box_dict['version'] = box_data.version
            if 'url' in update_data:
                box_dict['url'] = box_data.url
            
            box_dict['updated_at'] = datetime.now().isoformat()
            # Ensure metadata fields exist in stored JSON
            if 'is_shared' not in box_dict:
                box_dict['is_shared'] = False
            if 'owner_id' not in box_dict:
                box_dict['owner_id'] = self.user_id if self.user_id else None
            
            # Save using atomic write
            self.file_service.atomic_write_json(file_path, box_dict)
            
            return Box(**box_dict)
            
        except BoxServiceError:
            raise
        except Exception as e:
            raise BoxServiceError(f"Failed to update box {box_id}: {str(e)}")
    
    def delete_box(self, box_id: str) -> bool:
        """
        Delete a box.
        
        Args:
            box_id: Box ID
            
        Returns:
            True if deleted, False if not found
            
        Raises:
            BoxServiceError: If deletion fails or trying to delete shared resource
        """
        try:
            # Prevent deleting shared resources in public mode
            if self.user_id:
                user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{box_id}.json"
                if not user_file.exists():
                    raise BoxServiceError("Cannot delete shared resources")
                user_file.unlink()
                return True
            else:
                file_path = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
                if not file_path.exists():
                    return False
                file_path.unlink()
                return True
            
        except BoxServiceError:
            raise
        except Exception as e:
            raise BoxServiceError(f"Failed to delete box {box_id}: {str(e)}")
    
    def list_boxes(self) -> List[BoxSummary]:
        """
        List all boxes (merged shared + user-specific).
        Filters based on show_shared_resources preference.
        
        Returns:
            List of box summaries with is_shared and owner_id fields
        """
        try:
            # Use merge_resources helper (same as plugins/provisioners/triggers)
            def load_box_summary(file_path: Path) -> dict:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            merged_data = self.file_service.merge_resources(
                user_id=self.user_id,
                resource_type="boxes",
                loader_func=load_box_summary
            )
            
            # Convert to BoxSummary instances
            boxes = []
            
            # Load favorites if user is authenticated
            favorite_ids = []
            if self.user_id:
                from .preference_service import PreferenceService
                pref_service = PreferenceService(self.user_id)
                favorite_ids = pref_service.get_favorites('boxes')
            
            for data in merged_data:
                box = BoxSummary(**data)
                
                # Filter based on preferences
                # Show resource if: not shared, OR show_shared=True, OR is a favorite
                if box.is_shared and not self.show_shared and box.id not in favorite_ids:
                    continue
                
                boxes.append(box)
            
            return boxes
            
        except Exception as e:
            raise BoxServiceError(f"Failed to list boxes: {str(e)}")
    
    def get_boxes_for_api(self) -> List[Dict]:
        """
        Get boxes formatted for the existing API.
        
        Returns:
            List of boxes in API format
        """
        try:
            boxes = self.list_boxes()
            
            return [
                {
                    "name": box.name,
                    "description": box.description,
                    "provider": box.provider
                }
                for box in boxes
            ]
            
        except Exception as e:
            raise BoxServiceError(f"Failed to get boxes for API: {str(e)}")
    
    def copy_shared_box(self, box_id: str) -> Box:
        """
        Create a copy of a shared box in user's directory.
        User can then edit/customize their copy.
        
        Args:
            box_id: ID of the shared box to copy
            
        Returns:
            Copied box with new ID
            
        Raises:
            BoxServiceError: If box not found, not shared, or user_id not set
        """
        if not self.user_id:
            raise BoxServiceError("Cannot copy boxes in self-hosted mode")
        
        try:
            # Load shared box
            shared_file = self.file_service.get_shared_data_path("boxes") / f"{box_id}.json"
            
            if not shared_file.exists():
                raise BoxServiceError(f"Shared box {box_id} not found")
            
            with open(shared_file, 'r', encoding='utf-8') as f:
                box_data = json.load(f)
            
            # Verify it's a shared resource
            if not box_data.get("is_shared", False):
                raise BoxServiceError("Can only copy shared resources")
            
            # Generate new ID for the copy
            new_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create copy with new metadata
            box_copy = {
                **box_data,
                "id": new_id,
                "name": f"{box_data['name']} (Copy)",
                "is_shared": False,
                "owner_id": self.user_id,
                "source_id": box_id,  # Track original shared resource
                "created_at": now,
                "updated_at": now
            }
            
            # Save to user directory using atomic write
            user_file = self.file_service.get_user_data_path(self.user_id, "boxes") / f"{new_id}.json"
            self.file_service.atomic_write_json(user_file, box_copy)
            
            return Box(**box_copy)
            
        except Exception as e:
            raise BoxServiceError(f"Failed to copy box: {str(e)}")    
    def get_copies_of_shared_resource(self, source_id: str) -> List[Box]:
        """
        Get all user's copies of a specific shared resource.
        
        Args:
            source_id: ID of the original shared resource
            
        Returns:
            List of boxes that were copied from the specified shared resource
            
        Raises:
            BoxServiceError: If user_id not set
        """
        if not self.user_id:
            return []  # Self-hosted mode has no copies
        
        try:
            # List all user boxes and filter by source_id
            all_boxes = self.list_boxes()
            copies = [b for b in all_boxes if b.source_id == source_id]
            return copies
            
        except Exception as e:
            raise BoxServiceError(f"Failed to get copies: {str(e)}")
