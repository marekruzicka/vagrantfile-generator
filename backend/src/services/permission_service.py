"""
Permission Service.

Handles permission checks for resource access control.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for checking user permissions on resources."""
    
    def can_edit_resource(
        self,
        resource_owner_id: Optional[str],
        current_user_id: Optional[str],
        is_shared: bool = False
    ) -> bool:
        """
        Check if a user can edit a resource.
        
        Args:
            resource_owner_id: ID of the resource owner (None for shared resources)
            current_user_id: ID of the current user (None for unauthenticated)
            is_shared: Whether the resource is a shared system resource
            
        Returns:
            bool: True if user can edit the resource, False otherwise
        """
        # Shared resources are read-only for all users
        if is_shared:
            logger.debug(f"Edit denied: Resource is shared (read-only)")
            return False
        
        # In self-hosted mode (current_user_id is None), all resources are editable
        if current_user_id is None:
            logger.debug("Edit allowed: Self-hosted mode (no authentication)")
            return True
        
        # User can only edit their own resources
        can_edit = resource_owner_id == current_user_id
        if not can_edit:
            logger.warning(
                f"Edit denied: User {current_user_id} attempted to edit "
                f"resource owned by {resource_owner_id}"
            )
        return can_edit
    
    def can_delete_resource(
        self,
        resource_owner_id: Optional[str],
        current_user_id: Optional[str],
        is_shared: bool = False
    ) -> bool:
        """
        Check if a user can delete a resource.
        
        Args:
            resource_owner_id: ID of the resource owner (None for shared resources)
            current_user_id: ID of the current user (None for unauthenticated)
            is_shared: Whether the resource is a shared system resource
            
        Returns:
            bool: True if user can delete the resource, False otherwise
        """
        # Shared resources cannot be deleted by users
        if is_shared:
            logger.debug(f"Delete denied: Resource is shared (system resource)")
            return False
        
        # In self-hosted mode (current_user_id is None), all resources are deletable
        if current_user_id is None:
            logger.debug("Delete allowed: Self-hosted mode (no authentication)")
            return True
        
        # User can only delete their own resources
        can_delete = resource_owner_id == current_user_id
        if not can_delete:
            logger.warning(
                f"Delete denied: User {current_user_id} attempted to delete "
                f"resource owned by {resource_owner_id}"
            )
        return can_delete
    
    def can_view_resource(
        self,
        resource_owner_id: Optional[str],
        current_user_id: Optional[str],
        is_shared: bool = False
    ) -> bool:
        """
        Check if a user can view a resource.
        
        Args:
            resource_owner_id: ID of the resource owner (None for shared resources)
            current_user_id: ID of the current user (None for unauthenticated)
            is_shared: Whether the resource is a shared system resource
            
        Returns:
            bool: True if user can view the resource, False otherwise
        """
        # Shared resources are viewable by all users
        if is_shared:
            return True
        
        # In self-hosted mode, all resources are viewable
        if current_user_id is None:
            return True
        
        # User can view their own resources
        return resource_owner_id == current_user_id


# Global permission service instance
permission_service = PermissionService()
