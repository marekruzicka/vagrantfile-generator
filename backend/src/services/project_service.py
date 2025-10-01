"""
ProjectService for Vagrantfile GUI Generator.

This service handles all CRUD operations for projects, including persistence
to JSON files and business logic validation.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models import Project, ProjectCreate, ProjectUpdate, ProjectSummary, VirtualMachine, NetworkInterface, DeploymentStatus, PluginConfiguration


class ProjectNotFoundError(Exception):
    """Raised when a project is not found."""
    pass


class ProjectService:
    """Service class for managing Project entities."""

    def __init__(self, data_dir: str = "data/projects"):
        """
        Initialize the ProjectService.
        
        Args:
            data_dir: Directory where project JSON files are stored
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_file_path(self, project_id: UUID) -> Path:
        """Get the file path for a project's JSON file."""
        return self.data_dir / f"{project_id}.json"

    def _construct_vm_without_validation(self, vm_data: Dict[str, Any]) -> VirtualMachine:
        """Construct a VirtualMachine without validation for backward compatibility."""
        # Handle network interfaces separately
        network_interfaces = []
        if 'network_interfaces' in vm_data:
            for ni_data in vm_data['network_interfaces']:
                network_interfaces.append(NetworkInterface.construct(**ni_data))
            vm_data = {**vm_data, 'network_interfaces': network_interfaces}
        
        return VirtualMachine.construct(**vm_data)

    def _load_project_from_file(self, project_id: UUID) -> Project:
        """Load a project from its JSON file with minimal validation for backward compatibility."""
        file_path = self._get_project_file_path(project_id)
        
        if not file_path.exists():
            raise ProjectNotFoundError(f"Project {project_id} not found")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert datetime strings to datetime objects if they exist
            if 'created_at' in data and isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
            if 'updated_at' in data and isinstance(data['updated_at'], str):
                data['updated_at'] = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
            
            # Handle VMs separately to avoid validation issues
            vms = []
            if 'vms' in data:
                for vm_data in data['vms']:
                    vms.append(self._construct_vm_without_validation(vm_data))
                data = {**data, 'vms': vms}
            
            # Handle global_plugins separately to avoid validation issues
            plugins = []
            if 'global_plugins' in data:
                for plugin_data in data['global_plugins']:
                    plugins.append(PluginConfiguration.construct(**plugin_data))
                data = {**data, 'global_plugins': plugins}
            
            # Use construct() to create model without validation for existing data
            # This maintains backward compatibility with legacy projects
            return Project.construct(**data)
        except (json.JSONDecodeError, ValueError) as e:
            raise ValueError(f"Invalid project data in {file_path}: {e}")

    def _save_project_to_file(self, project: Project) -> None:
        """Save a project to its JSON file."""
        file_path = self._get_project_file_path(project.id)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict and save
        data = project.dict()
        
        # Custom JSON encoder for datetime and UUID
        def json_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            elif isinstance(obj, UUID):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=json_encoder, ensure_ascii=False)

    def create_project(self, project_data: ProjectCreate) -> Project:
        """
        Create a new project.
        
        Args:
            project_data: Project creation data
            
        Returns:
            Created Project instance
            
        Raises:
            ValueError: If project name already exists
        """
        # Check for duplicate names
        existing_projects = self.list_projects()
        for existing in existing_projects:
            if existing.name == project_data.name:
                raise ValueError(f"Project with name '{project_data.name}' already exists")
        
        # Create new project
        project = Project(
            name=project_data.name,
            description=project_data.description,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save to file
        self._save_project_to_file(project)
        
        return project

    def get_project(self, project_id: UUID) -> Project:
        """
        Get a project by ID.
        
        Args:
            project_id: Project UUID
            
        Returns:
            Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        return self._load_project_from_file(project_id)

    def update_project(self, project_id: UUID, project_data: ProjectUpdate) -> Project:
        """
        Update an existing project.
        
        Args:
            project_id: Project UUID
            project_data: Updated project data
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If validation fails
        """
        # Load existing project
        project = self._load_project_from_file(project_id)
        
        # Check for name conflicts with other projects
        if project_data.name != project.name:
            existing_projects = self.list_projects()
            for existing in existing_projects:
                if existing.id != project_id and existing.name == project_data.name:
                    raise ValueError(f"Project with name '{project_data.name}' already exists")
        
        # Update fields
        project.name = project_data.name
        project.description = project_data.description
        project.vms = project_data.vms
        project.global_plugins = project_data.global_plugins
        project.update_timestamp()
        
        # Save updated project
        self._save_project_to_file(project)
        
        return project

    def update_deployment_status(self, project_id: UUID, deployment_status: DeploymentStatus) -> Project:
        """
        Update a project's deployment status.
        
        Args:
            project_id: Project UUID
            deployment_status: New deployment status
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        # Load existing project
        project = self._load_project_from_file(project_id)
        
        # Update deployment status
        project.deployment_status = deployment_status
        project.update_timestamp()
        
        # Save updated project
        self._save_project_to_file(project)
        
        return project

    def delete_project(self, project_id: UUID) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: Project UUID
            
        Returns:
            True if project was deleted, False if not found
            
        Raises:
            ValueError: If project is locked (ready_to_deploy or deployed)
        """
        file_path = self._get_project_file_path(project_id)
        
        if not file_path.exists():
            return False
        
        # Check if project is locked
        try:
            project = self._load_project_from_file(project_id)
            if project.deployment_status == DeploymentStatus.READY:
                status_value = project.deployment_status.value if hasattr(project.deployment_status, 'value') else project.deployment_status
                raise ValueError(f"Cannot delete project '{project.name}' - project is locked in {status_value} status")
        except ProjectNotFoundError:
            return False
        
        try:
            file_path.unlink()
            return True
        except OSError:
            return False

    def list_projects(self) -> List[ProjectSummary]:
        """
        List all projects.
        
        Returns:
            List of ProjectSummary instances
        """
        projects = []
        
        # Scan for JSON files in data directory
        for file_path in self.data_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Create ProjectSummary from the data
                project_summary = ProjectSummary(
                    id=data['id'],
                    name=data['name'],
                    description=data['description'],
                    created_at=datetime.fromisoformat(data['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')),
                    vm_count=len(data.get('vms', [])),
                    deployment_status=DeploymentStatus(data.get('deployment_status', 'draft'))
                )
                
                projects.append(project_summary)
                
            except (json.JSONDecodeError, KeyError, ValueError):
                # Skip invalid files
                continue
        
        # Sort by creation date (newest first)
        projects.sort(key=lambda p: p.created_at, reverse=True)
        
        return projects

    def list_projects_by_status(self, deployment_status: DeploymentStatus) -> List[ProjectSummary]:
        """
        List projects filtered by deployment status.
        
        Args:
            deployment_status: Status to filter by
            
        Returns:
            List of ProjectSummary instances with matching status
        """
        all_projects = self.list_projects()
        return [p for p in all_projects if p.deployment_status == deployment_status]

    def add_vm_to_project(self, project_id: UUID, vm: VirtualMachine) -> Project:
        """
        Add a VM to a project.
        
        Args:
            project_id: Project UUID
            vm: VirtualMachine instance to add
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If VM name conflicts
        """
        project = self._load_project_from_file(project_id)
        project.add_vm(vm)
        self._save_project_to_file(project)
        return project

    def update_vm_in_project(self, project_id: UUID, vm_name: str, vm_data: Dict[str, Any]) -> Project:
        """
        Update a VM in a project.
        
        Args:
            project_id: Project UUID
            vm_name: Name of VM to update
            vm_data: Updated VM data
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If VM not found in project
        """
        project = self._load_project_from_file(project_id)
        
        vm = project.get_vm(vm_name)
        if not vm:
            raise ValueError(f"VM '{vm_name}' not found in project")
        
        # Update VM fields
        for field, value in vm_data.items():
            if hasattr(vm, field):
                setattr(vm, field, value)
        
        project.update_timestamp()
        self._save_project_to_file(project)
        
        return project

    def remove_vm_from_project(self, project_id: UUID, vm_name: str) -> Project:
        """
        Remove a VM from a project.
        
        Args:
            project_id: Project UUID
            vm_name: Name of VM to remove
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If VM not found in project
        """
        project = self._load_project_from_file(project_id)
        
        if not project.remove_vm(vm_name):
            raise ValueError(f"VM '{vm_name}' not found in project")
        
        self._save_project_to_file(project)
        return project

    def validate_project(self, project_id: UUID) -> Dict[str, Any]:
        """
        Validate a project configuration.
        
        Args:
            project_id: Project UUID
            
        Returns:
            Dictionary with validation results
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
        """
        project = self._load_project_from_file(project_id)
        
        is_valid, errors, warnings = project.validate_for_generation()
        
        return {
            "is_valid": is_valid,
            "errors": errors,
            "warnings": warnings,
            "vm_count": len(project.vms),
            "network_interfaces_count": sum(len(vm.network_interfaces) for vm in project.vms)
        }

    def project_exists(self, project_id: UUID) -> bool:
        """
        Check if a project exists.
        
        Args:
            project_id: Project UUID
            
        Returns:
            True if project exists, False otherwise
        """
        file_path = self._get_project_file_path(project_id)
        return file_path.exists()

    def get_project_count(self) -> int:
        """Get the total number of projects."""
        return len(list(self.data_dir.glob("*.json")))

    def add_plugin_to_project(self, project_id: UUID, plugin: 'PluginConfiguration') -> Project:
        """
        Add a plugin to a project's global plugins.
        
        Args:
            project_id: Project UUID
            plugin: PluginConfiguration instance to add
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If plugin name conflicts
        """
        project = self._load_project_from_file(project_id)
        
        # Check if plugin already exists
        if any(p.name == plugin.name for p in project.global_plugins):
            raise ValueError(f"Plugin '{plugin.name}' already exists in project")
        
        project.global_plugins.append(plugin)
        project.update_timestamp()
        self._save_project_to_file(project)
        return project

    def update_plugin_in_project(self, project_id: UUID, plugin_name: str, plugin: 'PluginConfiguration') -> Project:
        """
        Update a plugin in a project's global plugins.
        
        Args:
            project_id: Project UUID
            plugin_name: Name of plugin to update
            plugin: Updated PluginConfiguration instance
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If plugin not found in project
        """
        project = self._load_project_from_file(project_id)
        
        # Find the plugin index
        plugin_index = None
        for i, p in enumerate(project.global_plugins):
            if p.name == plugin_name:
                plugin_index = i
                break
        
        if plugin_index is None:
            raise ValueError(f"Plugin '{plugin_name}' not found in project")
        
        # Update the plugin
        project.global_plugins[plugin_index] = plugin
        project.update_timestamp()
        self._save_project_to_file(project)
        
        return project

    def remove_plugin_from_project(self, project_id: UUID, plugin_name: str) -> Project:
        """
        Remove a plugin from a project's global plugins.
        
        Args:
            project_id: Project UUID
            plugin_name: Name of plugin to remove
            
        Returns:
            Updated Project instance
            
        Raises:
            ProjectNotFoundError: If project doesn't exist
            ValueError: If plugin not found in project
        """
        project = self._load_project_from_file(project_id)
        
        # Find and remove the plugin
        original_count = len(project.global_plugins)
        project.global_plugins = [p for p in project.global_plugins if p.name != plugin_name]
        
        if len(project.global_plugins) == original_count:
            raise ValueError(f"Plugin '{plugin_name}' not found in project")
        
        project.update_timestamp()
        self._save_project_to_file(project)
        return project