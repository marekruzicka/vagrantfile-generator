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


class BoxServiceError(Exception):
    """Custom exception for box service errors."""
    pass


class BoxService:
    """Service for handling box operations."""
    
    def __init__(self, base_directory: str = "data"):
        """
        Initialize the box service.
        
        Args:
            base_directory: Base directory for storing box files
        """
        self.base_directory = Path(base_directory)
        self.boxes_directory = self.base_directory / "boxes"
        self.boxes_file = self.boxes_directory / "boxes.json"
        
        # Create directories if they don't exist
        self._ensure_directories()
        
        # Initialize with default boxes if file doesn't exist
        self._initialize_default_boxes()
    
    def _ensure_directories(self):
        """Ensure all required directories exist."""
        self.boxes_directory.mkdir(parents=True, exist_ok=True)
    
    def _initialize_default_boxes(self):
        """Initialize with default boxes if no boxes file exists."""
        if not self.boxes_file.exists():
            default_boxes = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/ubuntu2204",
                    "description": "Ubuntu 22.04 LTS (Jammy Jellyfish)",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/ubuntu2004",
                    "description": "Ubuntu 20.04 LTS (Focal Fossa)",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/centos7",
                    "description": "CentOS 7",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/debian12",
                    "description": "Debian 12 (Bookworm)",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/alpine318",
                    "description": "Alpine Linux 3.18",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "generic/fedora38",
                    "description": "Fedora 38",
                    "provider": "libvirt",
                    "version": None,
                    "url": None,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            ]
            
            self._save_boxes(default_boxes)
    
    def _load_boxes(self) -> List[Dict]:
        """Load boxes from the JSON file."""
        try:
            if not self.boxes_file.exists():
                return []
            
            with open(self.boxes_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('boxes', [])
                
        except Exception as e:
            raise BoxServiceError(f"Failed to load boxes: {str(e)}")
    
    def _save_boxes(self, boxes: List[Dict]):
        """Save boxes to the JSON file."""
        try:
            data = {
                "boxes": boxes,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(self.boxes_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            raise BoxServiceError(f"Failed to save boxes: {str(e)}")
    
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
            boxes = self._load_boxes()
            
            # Check if box name already exists
            if any(box['name'] == box_data.name for box in boxes):
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
                "created_at": now,
                "updated_at": now
            }
            
            boxes.append(box_dict)
            self._save_boxes(boxes)
            
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
            boxes = self._load_boxes()
            
            for box_dict in boxes:
                if box_dict['id'] == box_id:
                    return Box(**box_dict)
            
            return None
            
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
            BoxServiceError: If update fails
        """
        try:
            boxes = self._load_boxes()
            
            for i, box_dict in enumerate(boxes):
                if box_dict['id'] == box_id:
                    # Check if name is being changed and doesn't conflict
                    if (box_data.name and box_data.name != box_dict['name'] and 
                        any(box['name'] == box_data.name for box in boxes)):
                        raise BoxServiceError(f"Box with name '{box_data.name}' already exists")
                    
                    # Update fields - handle optional fields specially
                    if box_data.name is not None:
                        box_dict['name'] = box_data.name
                    if box_data.description is not None:
                        box_dict['description'] = box_data.description
                    if box_data.provider is not None:
                        box_dict['provider'] = box_data.provider
                    
                    # For optional fields, update if explicitly provided (including None)
                    # Check if field was explicitly set in the request
                    update_data = box_data.dict(exclude_unset=True)
                    if 'version' in update_data:
                        box_dict['version'] = box_data.version
                    if 'url' in update_data:
                        box_dict['url'] = box_data.url
                    
                    box_dict['updated_at'] = datetime.now().isoformat()
                    
                    boxes[i] = box_dict
                    self._save_boxes(boxes)
                    
                    return Box(**box_dict)
            
            return None
            
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
            BoxServiceError: If deletion fails
        """
        try:
            boxes = self._load_boxes()
            
            for i, box_dict in enumerate(boxes):
                if box_dict['id'] == box_id:
                    del boxes[i]
                    self._save_boxes(boxes)
                    return True
            
            return False
            
        except Exception as e:
            raise BoxServiceError(f"Failed to delete box {box_id}: {str(e)}")
    
    def list_boxes(self) -> List[BoxSummary]:
        """
        List all boxes.
        
        Returns:
            List of box summaries
        """
        try:
            boxes = self._load_boxes()
            
            return [
                BoxSummary(
                    id=box['id'],
                    name=box['name'],
                    description=box['description'],
                    provider=box['provider']
                )
                for box in boxes
            ]
            
        except Exception as e:
            raise BoxServiceError(f"Failed to list boxes: {str(e)}")
    
    def get_boxes_for_api(self) -> List[Dict]:
        """
        Get boxes formatted for the existing API.
        
        Returns:
            List of boxes in API format
        """
        try:
            boxes = self._load_boxes()
            
            return [
                {
                    "name": box['name'],
                    "description": box['description'],
                    "provider": box['provider']
                }
                for box in boxes
            ]
            
        except Exception as e:
            raise BoxServiceError(f"Failed to get boxes for API: {str(e)}")